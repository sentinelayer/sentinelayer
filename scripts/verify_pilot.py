"""Owned-host signed-policy probes; credentials remain in platform secrets."""
import copy
import concurrent.futures
import math
import uuid
from collections import Counter
from datetime import UTC, datetime
import json
import os
import time

import httpx
import pyotp

POLICY_ID = "6f01d176-58df-4e6a-bbd0-5be014259cee"
DENY = "/__sentinel_policy_probe__"
HOT = "/__sentinel_policy_hot_update__"


def transport_failure_code(error):
    # Exception messages can include credentials/URLs. Emit only type and errno.
    root = error
    for _ in range(10):
        if root.__cause__ is None:
            break
        root = root.__cause__
    code = getattr(root, "errno", None)
    return type(root).__name__ + (f":{code}" if isinstance(code, int) else "")


def revoke_owner_session(client, token):
    try:
        response = client.post("/api/v1/auth/logout", json={})
        if response.status_code == 200:
            return "api"
    except httpx.RequestError:
        pass
    # Private verifier only: revoke this verified token if public egress fails.
    # No credentials or tokens are emitted; API runtime never gets this DB URL.
    import jwt
    from sqlalchemy import create_engine, text
    claims = jwt.decode(token, os.environ["JWT_SECRET"], algorithms=["HS256"],
                        options={"require": ["exp", "sub", "tenant_id", "jti"]})
    if os.getenv("SL_PILOT_VERIFY") != "1" or claims["tenant_id"] != "sentinel-pilot":
        raise ValueError("Private session cleanup requires the owned pilot tenant")
    database = create_engine(os.environ["MIGRATION_DATABASE_URL"], pool_pre_ping=True)
    try:
        with database.begin() as connection:
            result = connection.execute(text("""
                UPDATE auth_sessions SET revoked_at=CURRENT_TIMESTAMP, revoke_reason='pilot_cleanup'
                WHERE token_id=:jti AND user_id=:uid AND tenant_id=:tenant
                  AND user_id IN (SELECT id FROM users WHERE email=:email AND tenant_id=:tenant)
            """), dict(jti=claims["jti"], uid=claims["sub"], tenant=claims["tenant_id"],
                       email=os.environ["PILOT_ADMIN_EMAIL"]))
            if result.rowcount != 1:
                raise RuntimeError("Private session cleanup could not verify one owned session")
        print("Owner session revoked through private database fallback PASS", flush=True)
        return "database"
    finally:
        database.dispose()


def capacity_probe(client, version, processing_samples=None):
    attempts = int(os.getenv("PILOT_CAPACITY_REQUESTS", "500"))
    concurrency = int(os.getenv("PILOT_CAPACITY_CONCURRENCY", "8"))
    if not 100 <= attempts <= 1000 or not 1 <= concurrency <= 32:
        raise ValueError("Deployed capacity probe exceeds its bounded budget")
    prefix = "/__sentinel_capacity_probe__/" + uuid.uuid4().hex
    def sample(index):
        started = time.perf_counter()
        try:
            response = client.get(f"{prefix}/{index}")
            raw = response.headers.get("X-SL-Gateway-Processing-Ms")
            try:
                processing = float(raw)
                if not math.isfinite(processing) or processing < 0:
                    processing = None
            except (TypeError, ValueError):
                processing = None
            return {"status": str(response.status_code), "processing_ms": processing,
                    "degraded": response.headers.get("X-SL-Gateway-Degraded") != "false",
                    "policy_match": response.headers.get("X-SL-Policy-Version") == f"{POLICY_ID}:{version}",
                    "stages": {stage: response.headers.get(f"X-SL-Gateway-{stage}-Ms") for stage in ("WAF", "Rate", "Policy", "Behavior", "Risk")},
                    "transport_failure": None, "wall_ms": (time.perf_counter() - started) * 1000}
        except httpx.RequestError as error:
            return {"status": type(error).__name__, "processing_ms": None, "degraded": False,
                    "policy_match": True, "stages": {}, "transport_failure": transport_failure_code(error), "wall_ms": (time.perf_counter() - started) * 1000}
    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        rows = list(executor.map(sample, range(attempts)))
    timings = sorted(row["processing_ms"] for row in rows if row["processing_ms"] is not None)
    if processing_samples is not None:
        processing_samples.extend(timings)
    stage_values = {}
    for stage in ("WAF", "Rate", "Policy", "Behavior", "Risk"):
        values = []
        for row in rows:
            try:
                value = float(row["stages"].get(stage))
                if math.isfinite(value) and value >= 0:
                    values.append(value)
            except (ValueError, TypeError):
                pass
        stage_values[stage] = sorted(values)
    p95 = timings[math.ceil(len(timings)*.95)-1] if timings else None
    report = {"attempts": attempts, "concurrency": concurrency,
              "elapsed_seconds": time.perf_counter() - started,
              "status_counts": dict(Counter(row["status"] for row in rows)),
              "transport_failure_codes": dict(Counter(row["transport_failure"] for row in rows if row["transport_failure"])),
              "failures": sum(row["status"] != "200" for row in rows),
              "degraded_responses": sum(row["degraded"] for row in rows),
              "policy_mismatches": sum(not row["policy_match"] for row in rows),
              "processing_samples": len(timings), "processing_p95_ms": p95,
              "stage_samples": {stage: len(values) for stage, values in stage_values.items()},
              "stage_p95_ms": {stage: values[math.ceil(len(values)*.95)-1] if values else None for stage, values in stage_values.items()},
              "client_wall_p95_ms": sorted(row["wall_ms"] for row in rows)[math.ceil(attempts*.95)-1],
              "scope": "Bounded deployed authenticated pilot through public HTTPS and signed tenant policy; not sustained capacity, HA or SLA certification."}
    report["processing_gate_pass"] = (len(timings) == attempts and p95 < 20 and not report["failures"]
                                      and not report["degraded_responses"] and not report["policy_mismatches"])
    print("PILOT_CAPACITY_EVIDENCE=" + json.dumps(report, sort_keys=True), flush=True)
    print("PILOT_CAPACITY_GATE=" + ("PASS" if report["processing_gate_pass"] else "FAIL"), flush=True)
    return report


def capacity_series(client, version):
    rounds = int(os.getenv("PILOT_CAPACITY_ROUNDS", "1"))
    attempts = int(os.getenv("PILOT_CAPACITY_REQUESTS", "500"))
    if not 1 <= rounds <= 20 or not 100 <= attempts <= 1000 or rounds * attempts > 20000:
        raise ValueError("Deployed capacity series exceeds its bounded budget")
    started = time.monotonic()
    reports = []
    timings = []
    for _ in range(rounds):
        # Stop scheduling more work after the five-minute series budget.
        if time.monotonic() - started >= 300:
            break
        reports.append(capacity_probe(client, version, timings))
        if reports[-1]["transport_failure_codes"]:
            break  # Preserve failure evidence and avoid another round of unreachable traffic.
    timings.sort()
    evidence = {
        "processing_samples": len(timings),
        "aggregate_processing_p95_ms": timings[math.ceil(len(timings)*.95)-1] if timings else None,
        "requested_rounds": rounds, "completed_rounds": len(reports),
        "attempts": sum(row["attempts"] for row in reports),
        "elapsed_seconds": time.monotonic() - started,
        "failures": sum(row["failures"] for row in reports),
        "degraded_responses": sum(row["degraded_responses"] for row in reports),
        "policy_mismatches": sum(row["policy_mismatches"] for row in reports),
        "transport_failure_codes": dict(sum((Counter(row["transport_failure_codes"]) for row in reports), Counter())),
        "round_processing_p95_ms": [row["processing_p95_ms"] for row in reports],
        "series_gate_pass": len(reports) == rounds and all(row["processing_gate_pass"] for row in reports),
        "scope": "Bounded authenticated deployed series; every round must pass independently. Aggregate percentile calculated from all received finite processing samples. No HA or SLA claim.",
    }
    print("PILOT_CAPACITY_SERIES=" + json.dumps(evidence, sort_keys=True), flush=True)
    return evidence


def wait_for_rate_telemetry(client, version):
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        try:
            response = client.get(DENY + "-boundary")
            value = float(response.headers.get("X-SL-Gateway-Rate-Ms", "nan"))
            if (response.status_code == 200 and math.isfinite(value) and value >= 0
                    and response.headers.get("X-SL-Policy-Version") == f"{POLICY_ID}:{version}"):
                print("Deployed trusted rate-stage telemetry ready PASS", flush=True)
                return
        except (httpx.RequestError, ValueError):
            pass
        time.sleep(2)
    raise RuntimeError("Rate-stage telemetry deployment did not converge")


def cleanup_previous_probe_session(api):
    start = os.getenv("PILOT_CLEANUP_PROBE_START")
    if not start:
        return
    lower = datetime.fromisoformat(start).replace(tzinfo=UTC)
    upper = datetime.fromisoformat(os.environ["PILOT_CLEANUP_PROBE_END"]).replace(tzinfo=UTC)
    if not 0 < (upper - lower).total_seconds() <= 10:
        raise ValueError("Previous probe cleanup requires a narrow recorded time window")
    rows = api("GET", "/auth/sessions")
    matches = [row for row in rows if not row["revoked"] and
               lower <= datetime.fromisoformat(row["created_at"]).replace(tzinfo=UTC) < upper]
    if len(matches) > 1:
        raise RuntimeError("Previous probe session is ambiguous")
    for row in matches:
        result = api("POST", f"/auth/sessions/{row['id']}/revoke", {})
        if not result.get("revoked"):
            raise RuntimeError("Previous probe cleanup failed")
    print(f"Previous recorded probe session cleanup PASS: revoked={len(matches)}", flush=True)


def main():
    if os.environ.get("SL_PILOT_VERIFY") != "1":
        raise ValueError("Pilot verification must be explicitly enabled")
    origin = os.environ["PILOT_BASE_URL"].rstrip("/")
    if origin != "https://sentinelayer-production-b882.up.railway.app":
        raise ValueError("Only the owned pilot origin is supported")
    with httpx.Client(base_url=origin, timeout=20, follow_redirects=False, trust_env=False,
                      limits=httpx.Limits(max_connections=32, max_keepalive_connections=32, keepalive_expiry=30)) as client:
        def api(method, path, body=None):
            response = client.request(method, "/api/v1" + path, json=body)
            if response.status_code != 200:
                print(f"PILOT_API_FAILURE method={method} path={path} status={response.status_code}", flush=True)
                raise RuntimeError("Authenticated pilot API operation failed")
            return response.json()

        credentials = {"email": os.environ["PILOT_ADMIN_EMAIL"],
                       "password": os.environ["PILOT_ADMIN_PASSWORD"]}
        challenge = api("POST", "/auth/login", credentials)
        assert challenge.get("mfa_required") and not challenge.get("access_token")
        credentials["mfa_code"] = pyotp.TOTP(os.environ["PILOT_ADMIN_MFA_SECRET"]).now()
        login = api("POST", "/auth/login", credentials)
        client.headers["Authorization"] = "Bearer " + login["access_token"]
        cleanup_mode = None
        capacity_ok = True
        try:
            owner = api("GET", "/auth/me")
            assert owner["is_admin"] and owner["mfa_enabled"] and owner["tenant_id"] == "sentinel-pilot"
            print("Owner MFA enforcement and authenticated pilot access PASS", flush=True)
            cleanup_previous_probe_session(api)
            # Read only: report registration/delivery state, never secrets or receiver URLs.
            hooks = api("GET", "/webhooks")
            deliveries = api("GET", "/webhooks/logs?limit=100")
            print("PILOT_ALERT_EVIDENCE=" + json.dumps({
                "registered_receivers": len(hooks),
                "receivers_with_secret": sum(bool(row.get("secret_configured")) for row in hooks),
                "recent_delivery_statuses": dict(Counter(row["status"] for row in deliveries)),
            }, sort_keys=True), flush=True)
            original = api("GET", f"/policies/{POLICY_ID}")
            rules = original["rules"]
            if isinstance(rules, str):
                rules = json.loads(rules)
            previous_version = original["version"]

            def probe(path, expected, version):
                response = client.get(path)
                if response.status_code != expected:
                    return False
                if response.headers.get("X-SL-Policy-Version") != f"{POLICY_ID}:{version}":
                    return False
                if expected == 403 and response.json().get("reason") != "signed_policy":
                    return False
                return True

            def wait_probe(path, expected, version):
                deadline = time.monotonic() + 35
                while time.monotonic() < deadline:
                    if probe(path, expected, version):
                        return
                    time.sleep(2)
                raise RuntimeError("Signed-policy probe did not converge")

            wait_probe(DENY, 403, previous_version)
            wait_probe(DENY + "-boundary", 200, previous_version)
            print("Signed deny rule and path boundary PASS", flush=True)
            if os.getenv("PILOT_HOT_UPDATE", "0") == "1":
                modified = copy.deepcopy(rules)
                modified["gateway"]["deny_path_prefixes"] = list(dict.fromkeys(
                    modified["gateway"].get("deny_path_prefixes", []) + [HOT]))
                new_version = api("POST", f"/policies/{POLICY_ID}/versions", {"rules": modified})["version"]
                try:
                    wait_probe(HOT, 403, new_version)
                    print(f"Live signed-policy hot update PASS: version {new_version}", flush=True)
                finally:
                    restored = api("POST", f"/policies/{POLICY_ID}/versions", {"rules": rules})
                previous_version = restored["version"]
                wait_probe(HOT, 200, previous_version)
                wait_probe(DENY, 403, previous_version)
                print(f"Original rules restored as higher signed version {previous_version} PASS", flush=True)
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                rows = api("GET", f"/policies/{POLICY_ID}/gateways")
                if any(row["gateway_id"] == "railway-pilot-edge-01" and row.get("state") == "reported"
                       and row.get("reported_version") == previous_version for row in rows):
                    print(f"Authenticated gateway receipt PASS: version {previous_version}", flush=True)
                    break
                client.get("/")
                time.sleep(2)
            else:
                raise RuntimeError("Gateway receipt did not converge")
            if os.getenv("PILOT_CAPACITY_PROBE", "0") == "1":
                wait_for_rate_telemetry(client, previous_version)
                capacity_ok = capacity_series(client, previous_version)["series_gate_pass"]
            print(f"PILOT_VERIFIED_VERSION={previous_version}", flush=True)
        finally:
            cleanup_mode = revoke_owner_session(client, login["access_token"])
        if cleanup_mode == "api":
            response = client.get("/api/v1/auth/me")
            assert response.status_code == 401
        print("Pilot verification completed; owner session revoked", flush=True)
        if not capacity_ok:
            raise RuntimeError("Deployed capacity series gate failed")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Pilot verification failed: {type(error).__name__}; credentials withheld", flush=True)
        raise SystemExit(1) from None
