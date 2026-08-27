from engine.risk.decision_matrix import DecisionMatrix
from engine.risk.engine import RiskEngine


def test_risk_calculate_block_path():
    eng = RiskEngine()
    out = eng.calculate({"failed_attempts": 10, "suspicious_ip": True, "multiple_tenants": True})
    assert out["score"] >= 30
    assert out["action"] in ("ALLOW", "MONITOR", "CHALLENGE", "BLOCK")


def test_decision_matrix_bounds():
    m = DecisionMatrix()
    assert m.get_action(10, 0.9) == "ALLOW"
    assert m.get_action(45, 0.5) == "MONITOR"
    assert m.get_action(45, 0.9) == "CHALLENGE"
    assert m.get_action(70, 0.2) == "MONITOR"
    assert m.get_action(70, 0.5) == "CHALLENGE"
    assert m.get_action(70, 0.9) == "BLOCK"
    assert m.get_action(90, 0.9) == "BLOCK"


def test_decision_matrix_invalid_values_fail_closed():
    m = DecisionMatrix()
    assert m.get_action(float("nan"), 0.9) == "BLOCK"
    assert m.get_action(50, float("inf")) == "BLOCK"
