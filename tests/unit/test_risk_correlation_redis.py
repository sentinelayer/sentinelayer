"""Run against real disposable Redis, never production state."""
import json
import os
import uuid
import pytest
from engine.risk.correlation import RiskCorrelation

@pytest.mark.integration
def test_bounded_correlation_preserves_types_counts_and_legacy(monkeypatch):
    url = os.getenv("TEST_ENGINE_REDIS_URL")
    if not url:
        pytest.skip("requires disposable Redis")
    correlation = RiskCorrelation(redis_url=url)
    tenant = "test-correlation-" + uuid.uuid4().hex
    key = correlation._key(tenant)
    clock = [2000000000.0]
    monkeypatch.setattr("engine.risk.correlation.time.time", lambda: clock[0])
    try:
        legacy = json.dumps({"type": "auth_failure", "timestamp": clock[0]})
        correlation._redis.zadd(key, {legacy: clock[0]})
        for index in range(1000):
            correlation.add_signal(tenant, "freq_critical", {})
        correlation.observe(tenant, ["waf_block", "waf_block"], {})
        result = correlation.correlate(tenant)
        assert result["signal_count"] == 1002
        assert result["unique_types"] == 3
        assert result["risk_multiplier"] == 1.5
        assert correlation._redis.zcard(key) == 3
        assert correlation._redis.hlen(key + ":counts") == 1
        clock[0] += 61
        assert correlation.correlate(tenant)["signal_count"] == 0
        correlation.add_signal(tenant, "auth_failure", {})
        assert correlation.correlate(tenant)["signal_count"] == 1
        assert correlation._redis.hlen(key + ":counts") == 1
        correlation.add_signal(tenant, "unknown-arbitrary-type", {})
        assert correlation._redis.zcard(key) == 1
    finally:
        correlation._redis.delete(key, key + ":counts")
