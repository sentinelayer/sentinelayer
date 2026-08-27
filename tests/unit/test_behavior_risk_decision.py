from engine.behavior import behavior_engine
from engine.risk.engine import RiskEngine


def test_risk_engine():
    context = {"failed_attempts": 5}
    result = RiskEngine().calculate(context)
    assert result["score"] > 0
    assert result["action"] in ("ALLOW", "MONITOR", "CHALLENGE", "BLOCK")


def test_behavior_engine():
    context = {"user_id": "test-user"}
    behavior_engine.track(context)
    behavior = behavior_engine.get_behavior("test-user")
    assert behavior["count"] > 0
