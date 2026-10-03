from fastapi.testclient import TestClient
from engine.risk import server
from engine.risk.correlation import CorrelationUnavailable


def test_async_shared_store_failure_preserves_critical_deny_and_normal_marker(monkeypatch):
    async def unavailable(*_args, **_kwargs):
        raise CorrelationUnavailable("test outage")
    monkeypatch.setattr(server.correlation, "observe_async", unavailable)
    with TestClient(server.app) as client:
        critical = client.post("/v1/score", json={"tenant_id": "failure-test", "context": {"criticality": "critical"}})
        assert critical.status_code == 200
        assert critical.json()["action"] == "BLOCK"
        assert critical.json()["factors"]["safety_reason"] == "shared_correlation_unavailable"
        normal = client.post("/v1/score", json={"tenant_id": "failure-test"})
        assert normal.status_code == 200
        assert "correlation_unavailable" in normal.json()["signals"]
        assert normal.json()["factors"]["correlation"]["unavailable"] is True
