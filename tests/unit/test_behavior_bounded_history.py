"""Capped frequency is disclosed; actual Redis invariants use integration tests."""
import json
from engine.behavior.server import BehaviorRequest, SharedBehaviorState


def test_capped_frequency_is_reported_as_lower_bound():
    class Store:
        def eval(self, script, number, key, now, cutoff, member):
            assert number == 1
            return [51, [json.dumps({"endpoint": "/safe"})] * 50]
    state = SharedBehaviorState()
    state.redis_client = Store()
    result = state.analyze(BehaviorRequest(endpoint="/safe", client_id="test"))
    assert result["frequency"]["count"] == 51
    assert result["frequency"]["count_is_lower_bound"] is True
    assert result["frequency"]["retained_count_limit"] == 51
    assert result["frequency"]["signals"] == ["freq_critical"]
    assert result["sequence"]["signals"] == []
