from scripts.probe_hosted_gateway import verify, read

import pytest


def test_hosted_probe_reports_only_tested_anonymous_boundaries():
    values = {
        "/health": (200, {"status": "healthy", "waf": "coraza"}),
        "/ready": (200, {"status": "ready"}),
        "/api/v1/admin/users": (401, {"code": "AUTH_REQUIRED"}),
        "/api/v1/keys": (401, {"code": "AUTH_REQUIRED"}),
        "/metrics": (401, {"detail": "Invalid metrics token"}),
    }
    assert verify(lambda path: values[path])["status"] == "PASS"
    assert "not authenticated tenant tests" in verify(lambda path: values[path])["scope"]


@pytest.mark.parametrize("path,status,payload", [
    ("/health", 503, {"status": "healthy", "waf": "coraza"}),
    ("/ready", 200, {"status": "not_ready"}),
    ("/api/v1/admin/users", 200, {"data": "leaked"}),
    ("/api/v1/keys", 403, {"status": "forbidden"}),
    ("/metrics", 200, {"data": "metrics"}),
])
def test_bad_hosted_responses_are_rejected(path, status, payload):
    values = {
        "/health": (200, {"status": "healthy", "waf": "coraza"}),
        "/ready": (200, {"status": "ready"}),
        "/api/v1/admin/users": (401, {}),
        "/api/v1/keys": (401, {}),
        "/metrics": (401, {}),
    }
    values[path] = status, payload
    with pytest.raises(ValueError):
        verify(lambda p: values[p])


def test_probe_disallows_unreviewed_paths():
    with pytest.raises(ValueError, match="PATH_FORBIDDEN"):
        read("/api/v1/auth/register")
