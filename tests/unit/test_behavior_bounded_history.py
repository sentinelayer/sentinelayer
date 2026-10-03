"""High traffic must retain total frequency while fetching bounded history."""
import json
from engine.behavior.server import BehaviorRequest, SharedBehaviorState


def test_large_history_preserves_frequency_and_bounds_transfer():
    class Pipeline:
        def zremrangebyscore(self, *args): return self
        def zadd(self, *args): return self
        def expire(self, *args): return self
        def zcard(self, *args): return self
        def zrange(self, key, start, stop):
            assert (start, stop) == (-50, -1)
            return self
        def execute(self):
            return [0, 1, True, 10000, [json.dumps({"endpoint": "/safe"})] * 50]
    class Store:
        def pipeline(self, transaction):
            assert transaction is True
            return Pipeline()
    state = SharedBehaviorState()
    state.redis_client = Store()
    result = state.analyze(BehaviorRequest(endpoint="/safe", client_id="test"))
    assert result["frequency"]["count"] == 10000
    assert result["frequency"]["signals"] == ["freq_critical"]
    assert result["sequence"]["signals"] == []
