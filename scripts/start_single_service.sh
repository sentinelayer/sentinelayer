#!/bin/sh
set -eu
printf '%s\n' "SentinelLayer single-service launcher active; gateway entrypoint enforced" >&2

if [ -z "${SL_RUN_STARTUP_MIGRATION:-}" ]; then
  SL_RUN_STARTUP_MIGRATION="$(python -c 'from control_plane.app.runtime import is_production; print("0" if is_production() else "1")')"
  export SL_RUN_STARTUP_MIGRATION
fi
python /app/scripts/validate_runtime_config.py

# Production migrations run in a separate job without sharing owner credentials
# with the API/worker processes. Development retains the optional startup migration.
if [ "${SL_RUN_STARTUP_MIGRATION:-1}" = "1" ]; then
  if [ -z "${MIGRATION_DATABASE_URL:-${DATABASE_URL:-}}" ]; then
    echo "DATABASE_URL is required for startup migration" >&2
    exit 1
  fi
  echo "running database migrations before starting security services"
  PYTHONPATH=/app alembic -c /app/alembic.ini upgrade head
fi

python -m uvicorn control_plane.app.main:app --host 127.0.0.1 --port 8005 &
CONTROL_PID=$!
python -m uvicorn engine.risk.server:app --host 127.0.0.1 --port 8090 &
RISK_PID=$!
python -m uvicorn engine.behavior.server:app --host 127.0.0.1 --port 8091 &
BEHAVIOR_PID=$!
python -m control_plane.app.workers.runner --loop &
WORKER_PID=$!

GATEWAY_PID=""
cleanup() {
  kill "$GATEWAY_PID" "$CONTROL_PID" "$RISK_PID" "$BEHAVIOR_PID" "$WORKER_PID" 2>/dev/null || true
  wait "$GATEWAY_PID" "$CONTROL_PID" "$RISK_PID" "$BEHAVIOR_PID" "$WORKER_PID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

ready() {
  python - "$1" <<'PYTHON'
import sys
import urllib.request

port = int(sys.argv[1])
path = "/api/v1/health/readiness" if port == 8005 else "/health"
try:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=1) as response:
        if response.status != 200:
            raise SystemExit(1)
except OSError:
    raise SystemExit(1)
PYTHON
}

attempt=0
while [ "$attempt" -lt 60 ]; do
  if ready 8005 && ready 8090 && ready 8091; then
    break
  fi
  attempt=$((attempt + 1))
  sleep 1
done

if ! ready 8005 || ! ready 8090 || ! ready 8091; then
  echo "internal services failed readiness" >&2
  exit 1
fi

/usr/local/bin/gateway &
GATEWAY_PID=$!
while :; do
  if ! kill -0 "$GATEWAY_PID" 2>/dev/null; then
    echo "gateway exited; stopping single-service runtime" >&2
    exit 1
  fi
  if ! kill -0 "$CONTROL_PID" 2>/dev/null || ! kill -0 "$RISK_PID" 2>/dev/null || ! kill -0 "$BEHAVIOR_PID" 2>/dev/null || ! kill -0 "$WORKER_PID" 2>/dev/null; then
    echo "internal service exited; stopping single-service runtime" >&2
    exit 1
  fi
  sleep 2
done
