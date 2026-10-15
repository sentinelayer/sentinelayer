"""Bounded real-HTTPS smoke check of the dedicated Railway gateway.

No credentials, customer data, writes or assumed production approval.
"""
from __future__ import annotations

import json
import ssl
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener

ORIGIN = "https://sentinelayer-production-635f.up.railway.app"
WAF_CHECKS = (
    "/api/v1/events?q=%3Cscript%3Ealert%281%29%3C%2Fscript%3E",
    "/api/v1/events?q=union%20select",
)
ALLOWED = {"/health", "/ready", "/api/v1/admin/users", "/api/v1/keys", "/metrics", *WAF_CHECKS}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        return None


def read(path: str, headers: dict[str, str] | None = None) -> tuple[int, dict]:
    if path not in ALLOWED:
        raise ValueError("HOSTED_PROBE_PATH_FORBIDDEN")
    request = Request(ORIGIN + path, headers={"Accept": "application/json",
                      "User-Agent": "SentineLayer-Hosted-Security-Probe/1.0", **(headers or {})})
    opener = build_opener(HTTPSHandler(context=ssl.create_default_context()), NoRedirect())
    try:
        with opener.open(request, timeout=15) as response:
            status, raw = response.status, response.read(4097)
    except HTTPError as error:
        status, raw = error.code, error.read(4097)
    if len(raw) > 4096:
        raise ValueError("HOSTED_PROBE_RESPONSE_TOO_LARGE")
    if not raw:
        return status, {}
    try:
        payload = json.loads(raw)
    except ValueError:
        raise ValueError("HOSTED_PROBE_RESPONSE_NOT_JSON") from None
    if not isinstance(payload, dict):
        raise ValueError("HOSTED_PROBE_RESPONSE_NOT_OBJECT")
    return status, payload


def verify(probe=read) -> dict:
    status, payload = probe("/health")
    if status != 200 or payload.get("status") != "healthy" or payload.get("waf") != "coraza":
        raise ValueError("HOSTED_GATEWAY_HEALTH_FAILED")
    status, payload = probe("/ready")
    if status != 200 or payload.get("status") != "ready":
        raise ValueError("HOSTED_GATEWAY_READINESS_FAILED")
    for path in ("/api/v1/admin/users", "/api/v1/keys"):
        if probe(path)[0] != 401:
            raise ValueError("HOSTED_ANONYMOUS_PRIVILEGED_ACCESS_NOT_DENIED")
    if probe("/metrics")[0] not in {401, 403}:
        raise ValueError("HOSTED_METRICS_NOT_PROTECTED")
    for path in WAF_CHECKS:
        status, attack = probe(path)
        if (status != 403 or attack.get("action") != "BLOCK"
                or not str(attack.get("reason", "")).startswith("waf_block rule=")):
            raise ValueError("HOSTED_WAF_REQUEST_NOT_BLOCKED")
    return {"status": "PASS", "origin": ORIGIN,
            "gateway": "HTTPS_HEALTH_AND_READY", "waf": "INITIALIZED",
            "anonymous_admin_and_keys": "DENIED",
            "anonymous_metrics": "DENIED", "waf_synthetic_xss_sqli": "BLOCKED",
            "scope": "Live HTTPS availability and anonymous security boundaries only; "
                     "not authenticated tenant tests, WAF effectiveness, high availability, "
                     "signed artifact provenance, backup restore or production acceptance"}


def main():
    print(json.dumps(verify(), sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as error:
        raise SystemExit("Hosted security probe failed: " + str(error)) from None
