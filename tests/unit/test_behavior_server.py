from fastapi.testclient import TestClient

from engine.behavior import behavior_engine
from engine.behavior.server import app


def test_behavior_analyze_requires_scope():
    with TestClient(app) as client:
        response = client.post("/v1/analyze", json={"endpoint": "/api/orders"})
        assert response.status_code == 400


def test_behavior_analyze_returns_frequency_signal():
    behavior_engine.user_behavior.clear()
    behavior_engine.sequences.clear()
    payload = {
        "tenant_id": "tenant-test",
        "client_id": "client-test",
        "endpoint": "/api/orders",
    }
    with TestClient(app) as client:
        for _ in range(21):
            response = client.post("/v1/analyze", json=payload)
            assert response.status_code == 200
        result = response.json()
        assert result["is_anomaly"] is True
        assert "freq_elevated" in result["signals"]
        assert result["engine_version"] == "1.0.0"


def test_behavior_rejects_oversized_endpoint():
    with TestClient(app) as client:
        response = client.post(
            "/v1/analyze",
            json={"tenant_id": "tenant-test", "client_id": "client-test", "endpoint": "x" * 2049},
        )
        assert response.status_code == 422
