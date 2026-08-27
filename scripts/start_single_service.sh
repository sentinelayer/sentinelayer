#!/bin/sh
set -eu

python -m uvicorn control_plane.app.main:app --host 127.0.0.1 --port 8005 &
CONTROL_PID=$!
python -m uvicorn engine.risk.server:app --host 127.0.0.1 --port 8090 &
RISK_PID=$!
python -m uvicorn engine.behavior.server:app --host 127.0.0.1 --port 8091 &
BEHAVIOR_PID=$!
python -m control_plane.app.workers.runner --loop &
WORKER_PID=$!

cleanup() {
  kill "$CONTROL_PID" "$RISK_PID" "$BEHAVIOR_PID" "$WORKER_PID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

ready() {
  python - "$1" <<'PY'
import socket
import sys

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.settimeout(1)
    try:
        sock.connect(("127.0.0.1", int(sys.argv[1])))
    except OSError:
        raise SystemExit(1)
PY
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

trap - INT TERM EXIT
exec /usr/local/bin/gateway
