"""Owned-host signed-policy probes; credentials remain in platform secrets."""
import copy
import json
import os
import time

import httpx
import pyotp

POLICY_ID = "6f01d176-58df-4e6a-bbd0-5be014259cee"
DENY = "/__sentinel_policy_probe__"
HOT = "/__sentinel_policy_hot_update__"


def main():
    if os.environ.get("SL_PILOT_VERIFY") != "1":
        raise ValueError("Pilot verification must be explicitly enabled")
    origin = os.environ["PILOT_BASE_URL"].rstrip("/")
    if origin != "https://sentinelayer-production-b882.up.railway.app":
        raise ValueError("Only the owned pilot origin is supported")
    with httpx.Client(base_url=origin, timeout=20, follow_redirects=False, trust_env=False) as client:
        def api(method, path, body=None):
            response = client.request(method, "/api/v1" + path, json=body)
            if response.status_code != 200:
                raise RuntimeError("Authenticated pilot API operation failed")
            return response.json()

        credentials = {"email": os.environ["PILOT_ADMIN_EMAIL"],
                       "password": os.environ["PILOT_ADMIN_PASSWORD"]}
        challenge = api("POST", "/auth/login", credentials)
        assert challenge.get("mfa_required") and not challenge.get("access_token")
        credentials["mfa_code"] = pyotp.TOTP(os.environ["PILOT_ADMIN_MFA_SECRET"]).now()
        login = api("POST", "/auth/login", credentials)
        client.headers["Authorization"] = "Bearer " + login["access_token"]
        owner = api("GET", "/auth/me")
        assert owner["is_admin"] and owner["mfa_enabled"] and owner["tenant_id"] == "sentinel-pilot"
        print("Owner MFA enforcement and authenticated pilot access PASS", flush=True)
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

        try:
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
            print(f"PILOT_VERIFIED_VERSION={previous_version}", flush=True)
        finally:
            api("POST", "/auth/logout", {})
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
        print("Pilot verification completed; owner session revoked", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Pilot verification failed: {type(error).__name__}; credentials withheld", flush=True)
        raise SystemExit(1) from None
