from __future__ import annotations

import gzip
import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Direct script execution must support parent-process API imports without PYTHONPATH.
sys.path.insert(0, str(ROOT))
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
    if os.getenv("E2E_HOST_POLICY") == "1":
        request_headers["Host"] = "a.example"
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
    policy_fixture = None
    try:
        if os.getenv("E2E_SIGNED_POLICY") == "1":
            from helpers.runtime_policy_fixture import RuntimePolicyFixture
            policy_fixture = RuntimePolicyFixture()
            env.update(policy_fixture.env)
            if os.getenv("E2E_HOST_POLICY") == "1":
                for name in ("GATEWAY_POLICY_URL", "GATEWAY_POLICY_API_KEY", "GATEWAY_POLICY_ID", "GATEWAY_POLICY_TENANT_ID"):
                    env.pop(name, None)
                env["GATEWAY_POLICY_BINDINGS_JSON"] = policy_fixture.host_bindings()
        processes.append(subprocess.Popen(["python3", "tests/helpers/e2e_upstream.py"], cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT))
        processes.append(subprocess.Popen(["python3", "-m", "engine.risk.server"], cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT))
        processes.append(subprocess.Popen(["python3", "-m", "engine.behavior.server"], cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT))
        wait_http("http://127.0.0.1:18080/health")
        wait_http("http://127.0.0.1:8090/health")
        wait_http("http://127.0.0.1:8091/health")
        processes.append(subprocess.Popen([gateway_bin], cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT))
        wait_http(f"http://127.0.0.1:{GATEWAY_PORT}/health")

        status, body, _ = request(f"http://127.0.0.1:{GATEWAY_PORT}/safe")
        assert status == 200, (status, body)
        safe_response = json.loads(body)
        assert safe_response["upstream"] is True
        assert safe_response["gateway_degraded"] == "false"
        assert safe_response["decision"] in {"ALLOW", "MONITOR"}

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
        if os.getenv("E2E_FAILURE_DRILL") == "1":
            import jwt
            from datetime import UTC, datetime, timedelta
            token = jwt.encode({"sub": "failure-drill", "tenant_id": "failure-drill",
                                "exp": datetime.now(UTC) + timedelta(minutes=5)}, env["JWT_SECRET"], algorithm="HS256")
            auth = {"Authorization": f"Bearer {token}"}
            # Terminate only engine processes created by this test. Keep the
            # upstream alive to distinguish a protected denial from an outage.
            for process, module in ((processes[1], "engine.risk.server"), (processes[2], "engine.behavior.server")):
                process.terminate()
                process.wait(timeout=5)
                status, body, _ = request(f"http://127.0.0.1:{GATEWAY_PORT}/api/v1/admin/drill", headers=auth)
                assert status == 403, (module, status, body)
                assert json.loads(body)["reason"].endswith("unavailable_fail_closed"), body
                normal_status, normal_body, _ = request(f"http://127.0.0.1:{GATEWAY_PORT}/safe")
                assert normal_status == 200
                assert json.loads(normal_body)["gateway_degraded"] == "true"
                assert request(f"http://127.0.0.1:{GATEWAY_PORT}/safe", attack,
                               {"Content-Type": "application/json"})[0] == 403
                processes.append(subprocess.Popen([sys.executable, "-m", module], cwd=ROOT, env=env,
                                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT))
                wait_http("http://127.0.0.1:8090/health" if "risk" in module else "http://127.0.0.1:8091/health")
                deadline = time.monotonic() + 15
                while request(f"http://127.0.0.1:{GATEWAY_PORT}/api/v1/admin/drill", headers=auth)[0] != 200:
                    assert time.monotonic() < deadline, module
                    time.sleep(.5)
            print("failure drill: risk and behavior outage deny critical traffic, preserve normal proxy/WAF, recover after restart")
        if policy_fixture:
            import jwt
            from datetime import UTC, datetime, timedelta
            status, body, response_headers = request(f"http://127.0.0.1:{GATEWAY_PORT}/policy-denied")
            assert status == 403 and json.loads(body)["reason"] == "signed_policy", (status, body)
            assert {k.lower(): v for k, v in response_headers.items()}["x-sl-policy-version"] == f"{policy_fixture.policy_id}:1"
            status, _, _ = request(f"http://127.0.0.1:{GATEWAY_PORT}/policy-denied-ish")
            assert status == 200, status
            foreign = jwt.encode({"sub": "foreign", "tenant_id": "other", "exp": datetime.now(UTC) + timedelta(minutes=2)}, env["JWT_SECRET"], algorithm="HS256")
            status, body, _ = request(f"http://127.0.0.1:{GATEWAY_PORT}/safe", headers={"Authorization": f"Bearer {foreign}"})
            assert status == 403 and json.loads(body)["code"] == "POLICY_TENANT", (status, body)

            def restart_gateway():
                processes[-1].terminate()
                processes[-1].wait(timeout=5)
                processes.append(subprocess.Popen([gateway_bin], cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT))
                wait_http(f"http://127.0.0.1:{GATEWAY_PORT}/health")

            deadline = time.monotonic() + 5
            while policy_fixture.delivery()["state"] != "reported":
                assert time.monotonic() < deadline, policy_fixture.delivery()
                time.sleep(.1)
            assert policy_fixture.delivery()["reported_version"] == 1
            if os.getenv("E2E_HOST_POLICY") == "1":
                assert request(f"http://127.0.0.1:{GATEWAY_PORT}/policy-denied", headers={"Host": "b.example"})[0] == 200
                assert request(f"http://127.0.0.1:{GATEWAY_PORT}/other-denied", headers={"Host": "b.example"})[0] == 403
                assert request(f"http://127.0.0.1:{GATEWAY_PORT}/safe", headers={"Host": "unknown.example"})[0] == 421
                assert request(f"http://127.0.0.1:{GATEWAY_PORT}/policy-denied",
                               headers={"X-Tenant-ID": "policy-other", "X-Forwarded-Host": "b.example"})[0] == 403
            assert request(f"http://127.0.0.1:{GATEWAY_PORT}/safe", headers={"X-API-Key": "unverified"})[0] == 401
            policy_fixture.monitor()
            deadline = time.monotonic() + 15
            while True:
                status, _, response_headers = request(f"http://127.0.0.1:{GATEWAY_PORT}/policy-denied")
                version = {k.lower(): v for k, v in response_headers.items()}.get("x-sl-policy-version")
                if status == 200 and version == f"{policy_fixture.policy_id}:2":
                    break
                assert time.monotonic() < deadline, (status, version)
                time.sleep(0.5)
            status, _, _ = request(f"http://127.0.0.1:{GATEWAY_PORT}/safe", attack, {"Content-Type": "application/json"})
            assert status == 403, status
            deadline = time.monotonic() + 5
            while policy_fixture.delivery()["reported_version"] != 2:
                assert time.monotonic() < deadline, policy_fixture.delivery()
                time.sleep(.1)
            assert policy_fixture.delivery()["state"] == "reported"
            policy_fixture.tamper.set()
            restart_gateway()
            status, body, _ = request(f"http://127.0.0.1:{GATEWAY_PORT}/safe")
            assert status == 503 and json.loads(body)["code"] == "POLICY_DEPENDENCY", (status, body)
            print("signed policy e2e: real API-key export, Python-to-Go signature, deny boundary, tenant binding, forged signature rejection, hot version update, authenticated receipt, and monitor WAF protection passed")
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
        if policy_fixture:
            policy_fixture.close()


if __name__ == "__main__":
    main()
