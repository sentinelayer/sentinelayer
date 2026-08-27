from __future__ import annotations

import gzip
import json
import os
import signal
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATEWAY_PORT = int(os.getenv("E2E_GATEWAY_PORT", "18000"))
UPSTREAM_PORT = int(os.getenv("E2E_UPSTREAM_PORT", "18080"))
REDIS_URL = os.getenv("E2E_REDIS_URL", "redis://127.0.0.1:6379/0")


def wait_http(url: str, timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status < 500:
                    return
        except Exception as exc:  # noqa: BLE001 - retry until process readiness deadline
            last_error = exc
        time.sleep(0.25)
    raise RuntimeError(f"service did not become ready: {url}: {last_error}")


def request(url: str, data: bytes | None = None, headers: dict[str, str] | None = None) -> tuple[int, bytes, dict[str, str]]:
    request_headers = {"Accept": "application/json", "User-Agent": "SentinelLayer-E2E/1.0"}
    request_headers.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=request_headers, method="POST" if data is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status, response.read(), dict(response.headers)
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(), dict(exc.headers)


def main() -> None:
    gateway_bin = os.getenv("GATEWAY_BIN", "/tmp/gateway-bin")
    env = os.environ.copy()
    env.update({
        "PYTHONPATH": str(ROOT),
        "SL_ENV": "test",
        "REDIS_URL": REDIS_URL,
        "E2E_UPSTREAM_PORT": str(UPSTREAM_PORT),
        "PORT": str(GATEWAY_PORT),
        "UPSTREAM_URL": f"http://127.0.0.1:{UPSTREAM_PORT}",
        "RISK_ENGINE_URL": "http://127.0.0.1:8090",
        "BEHAVIOR_ENGINE_URL": "http://127.0.0.1:8091",
        "JWT_SECRET": "ci-test-secret-min-32-chars-xxxxxx",
        "CRS_RULES_DIR": str(ROOT / "waf" / "rules"),
    })
    processes: list[subprocess.Popen[bytes]] = []
    try:
        processes.append(subprocess.Popen(["python3", "tests/helpers/e2e_upstream.py"], cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT))
        processes.append(subprocess.Popen(["python3", "-m", "engine.risk.server"], cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT))
        processes.append(subprocess.Popen(["python3", "-m", "engine.behavior.server"], cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT))
        wait_http("http://127.0.0.1:18080/health")
        wait_http("http://127.0.0.1:8090/health")
        wait_http("http://127.0.0.1:8091/health")
        processes.append(subprocess.Popen([gateway_bin], cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT))
        wait_http(f"http://127.0.0.1:{GATEWAY_PORT}/health")

        status, body, headers = request(f"http://127.0.0.1:{GATEWAY_PORT}/safe")
        assert status == 200, (status, body)
        assert json.loads(body)["upstream"] is True
        assert headers.get("X-SL-Decision") in {"ALLOW", "MONITOR"}

        attack = b'{"username":"admin\' OR 1=1 --"}'
        status, _, _ = request(f"http://127.0.0.1:{GATEWAY_PORT}/safe", attack, {"Content-Type": "application/json"})
        assert status == 403, status

        compressed = gzip.compress(attack)
        status, _, _ = request(f"http://127.0.0.1:{GATEWAY_PORT}/safe", compressed, {"Content-Type": "application/json", "Content-Encoding": "gzip"})
        assert status == 403, status

        status, _, _ = request(f"http://127.0.0.1:{GATEWAY_PORT}/api/v1/admin/secret")
        assert status == 401, status

        oversized = b"A" * (2 * 1024 * 1024 + 1)
        status, _, _ = request(f"http://127.0.0.1:{GATEWAY_PORT}/safe", oversized)
        assert status == 400, status
        print("gateway e2e: safe proxy, CRS body block, gzip body block, critical auth, and body limit passed")
    finally:
        for process in reversed(processes):
            if process.poll() is None:
                process.send_signal(signal.SIGTERM)
        for process in reversed(processes):
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


if __name__ == "__main__":
    main()
