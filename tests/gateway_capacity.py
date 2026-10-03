"""Run bounded, isolated local gateway capacity profiles with real Redis/engines.

GATEWAY_BIN and REDIS_BIN locate pre-built executables. No remote origin accepted.
"""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.benchmark import run_benchmark


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=5000)
    parser.add_argument("--concurrency", type=int, default=32)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tenant-profile", action="store_true", help="Simulate tenant-scoped risk correlation; not signed-policy validation")
    args = parser.parse_args()
    if not 1 <= args.iterations <= 100000 or not 1 <= args.concurrency <= 64:
        parser.error("bounded iterations/concurrency required")
    env = os.environ.copy()
    for key in list(env):
        if key.startswith(("GATEWAY_POLICY", "POLICY_SIGNING")) or key == "REDIS_ADDR":
            env.pop(key)
    env.update(SL_ENV="test", ENVIRONMENT="test", SL_ENFORCE_PROVENANCE="0",
        JWT_SECRET="capacity-test-secret-min-32-chars-xxxxxx", REDIS_URL="redis://127.0.0.1:16379/0",
        E2E_UPSTREAM_PORT="18080", PORT="18000", UPSTREAM_URL="http://127.0.0.1:18080",
        RISK_ENGINE_URL="http://127.0.0.1:8090", BEHAVIOR_ENGINE_URL="http://127.0.0.1:8091",
        CRS_RULES_DIR=str(ROOT / "waf/rules"), PYTHONPATH=str(ROOT))
    commands = [
        [os.getenv("REDIS_BIN", "redis-server"), "--port", "16379", "--save", "", "--appendonly", "no"],
        [sys.executable, "tests/helpers/e2e_upstream.py"],
        [sys.executable, "-m", "engine.risk.server"],
        [sys.executable, "-m", "engine.behavior.server"],
        [os.getenv("GATEWAY_BIN", "/tmp/gateway-bin")],
    ]
    processes = []
    with tempfile.TemporaryFile() as log, requests.Session() as session:
        session.trust_env = False
        try:
            for command in commands:
                processes.append(subprocess.Popen(command, cwd=ROOT, env=env, stdout=log, stderr=log))
            for port in (18080, 8090, 8091, 18000):
                deadline = time.monotonic() + 30
                while True:
                    if any(process.poll() is not None for process in processes):
                        raise RuntimeError("test-owned process exited before readiness")
                    try:
                        if session.get(f"http://127.0.0.1:{port}/health", timeout=1).status_code == 200:
                            break
                    except requests.RequestException:
                        pass
                    if time.monotonic() >= deadline:
                        raise RuntimeError("local readiness deadline exceeded")
                    time.sleep(.2)
            common = {"iterations": args.iterations, "concurrency": args.concurrency}
            baseline = run_benchmark("http://127.0.0.1:18080", prefix="/capacity-baseline", **common)
            gateway = run_benchmark("http://127.0.0.1:18000", prefix="/capacity-gateway",
                extra_headers={"X-Tenant-ID": "capacity-test-tenant"} if args.tenant_profile else None, **common)
            passed = (gateway["gateway_processing_samples"] == args.iterations
                and gateway["gateway_processing_p95_ms"] < 20 and not gateway["failures"] and not baseline["failures"] and not gateway["degraded_responses"])
            evidence = {"timestamp": datetime.now(UTC).isoformat(), "engine_workers": env.get("SL_ENGINE_WORKERS", "2"),
                "tenant_profile": args.tenant_profile, "baseline": baseline, "gateway": gateway, "local_processing_gate_pass": passed,
                "limitations": "Local synthetic distinct-path profile; no signed policy, sustained production capacity, HA or SLA claim."}
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(evidence, indent=2) + "\n")
            print(json.dumps(evidence, indent=2))
            return 0 if passed else 1
        finally:
            for process in reversed(processes):
                if process.poll() is None:
                    process.terminate()
            for process in reversed(processes):
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)

if __name__ == "__main__":
    raise SystemExit(main())
