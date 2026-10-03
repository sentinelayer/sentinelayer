"""Threshold equivalence, expiry, sequence and scope against disposable Redis."""
import os
import uuid
import pytest
from engine.behavior.server import BehaviorRequest, SharedBehaviorState

@pytest.mark.integration
def test_bounded_behavior_preserves_window_thresholds_and_scope(monkeypatch):
    url = os.getenv("TEST_ENGINE_REDIS_URL")
    if not url:
        pytest.skip("requires disposable Redis")
    monkeypatch.setenv("REDIS_URL", url)
    state = SharedBehaviorState()
    tenant = "behavior-test-" + uuid.uuid4().hex
    clock = [2000000000.0]
    monkeypatch.setattr("engine.behavior.server.time.time", lambda: clock[0])
    req = BehaviorRequest(tenant_id=tenant, client_id="actor-a", endpoint="/safe")
    other = BehaviorRequest(tenant_id=tenant, client_id="actor-b", endpoint="/safe")
    other_tenant = BehaviorRequest(tenant_id=tenant + "-other", client_id="actor-a", endpoint="/safe")
    keys = ["sl:behavior:actions:" + state._scoped_actor(r) for r in (req, other, other_tenant)]
    reference_times = []
    try:
        for index in range(1000):
            clock[0] += .01
            reference_times.append(clock[0])
            result = state.analyze(req)
            expected = [] if index < 20 else ["freq_elevated"] if index < 50 else ["freq_critical"]
            assert result["frequency"]["signals"] == expected
            assert result["frequency"]["count"] == min(index + 1, 51)
        assert state.redis_client.zcard(keys[0]) == 51
        assert result["frequency"]["count_is_lower_bound"] is True
        assert state.analyze(other)["frequency"]["count"] == 1
        assert state.analyze(other_tenant)["frequency"]["count"] == 1
        # Partial expiry must preserve exact threshold decisions as the window drains.
        for timestamp in (2000000309.75, 2000000309.9, 2000000311.0):
            clock[0] = timestamp
            result = state.analyze(req)
            reference_times = [t for t in reference_times if t > timestamp - 300] + [timestamp]
            reference = len(reference_times)
            expected = [] if reference <= 20 else ["freq_elevated"] if reference <= 50 else ["freq_critical"]
            assert result["frequency"]["signals"] == expected
        for endpoint in ("login", "add_payment", "coupon", "refund"):
            clock[0] += .1
            result = state.analyze(BehaviorRequest(tenant_id=tenant, client_id="actor-b", endpoint=endpoint))
        assert result["sequence"]["signals"] == ["sequence_fraud"]
        assert all(state.redis_client.zcard(key) <= 51 for key in keys)
    finally:
        state.redis_client.delete(*keys)
        state.redis_client.close()
