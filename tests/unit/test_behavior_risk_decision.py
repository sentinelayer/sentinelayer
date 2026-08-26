import pytest
from control_plane.risk.engine import risk_engine
from control_plane.behavior.engine import behavior_engine

def test_risk_engine():
    context = {"failed_attempts": 5}
    score = risk_engine.calculate(context)
    assert score > 0

def test_behavior_engine():
    context = {"user_id": "test-user"}
    behavior_engine.track(context)
    behavior = behavior_engine.get_behavior("test-user")
    assert behavior["count"] > 0
