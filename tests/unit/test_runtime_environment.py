import pytest
from fastapi.testclient import TestClient

from control_plane.app.runtime import is_production, runtime_environment
from control_plane.app.infrastructure.kms.client import KMSClient
from control_plane.app.domain.policy.signing import PolicySigning
from control_plane.app.workers import runner
from engine.behavior.server import SharedBehaviorState
from scripts.validate_runtime_config import validate


@pytest.mark.parametrize("name", ["SL_ENV", "ENVIRONMENT"])
@pytest.mark.parametrize("value", ["prod", "production", "PRODUCTION", " prod "])
def test_production_aliases_enable_security(name, value, monkeypatch):
    monkeypatch.delenv("SL_ENV", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.setenv(name, value)
    for key in ("KMS_KEY", "POLICY_SIGNING_PRIVATE_KEY", "REDIS_URL"):
        monkeypatch.delenv(key, raising=False)
    assert is_production()
    assert runtime_environment() == "production"
    assert "DATABASE_URL is required in production" in validate({name: value})
    with pytest.raises(RuntimeError, match="KMS_KEY"):
        KMSClient()
    with pytest.raises(RuntimeError, match="required in production"):
        PolicySigning()
    with pytest.raises(RuntimeError, match="REDIS_URL"):
        runner._redis_client()
    with pytest.raises(RuntimeError, match="REDIS_URL"):
        SharedBehaviorState()


def test_conflicting_environment_flags_fail_closed():
    assert is_production({"SL_ENV": "test", "ENVIRONMENT": "prod"})
    assert is_production({"SL_ENV": "prod", "ENVIRONMENT": "test"})
    assert runtime_environment({"SL_ENV": "test", "ENVIRONMENT": "prod"}) == "production"
    assert not is_production({})
    assert runtime_environment({}) == "development"


@pytest.mark.parametrize("name", ["SL_ENV", "ENVIRONMENT"])
def test_production_metrics_and_hsts_use_same_environment(name, monkeypatch):
    from control_plane.app.main import app
    monkeypatch.delenv("SL_ENV", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("METRICS_TOKEN", raising=False)
    monkeypatch.setenv(name, " prod ")
    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 503
    assert response.headers["Strict-Transport-Security"].startswith("max-age=")
