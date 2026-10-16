"""Unknown risk evidence must never fabricate a high-risk decision."""

from engine.risk.server import RiskRequest, _decision
from engine.risk.signal_catalog import SignalCatalog


def test_unknown_signal_has_no_measured_weight():
    catalog = SignalCatalog()
    assert catalog.get_weight("invented_future_signal") == 0


def test_unknown_signal_does_not_increase_risk_or_confidence():
    response = _decision(
        RiskRequest(signals=["unknown_a", "unknown_a", "unknown_b"]),
        {"risk_multiplier": 1.0, "signal_count": 0},
    )
    assert response.score == 0.0
    assert response.confidence == 0.4  # uncertainty discount, not a confidence boost
    assert response.factors["unknown_signals"] == ["unknown_a", "unknown_b"]
    assert response.factors["signal_weights"]["unknown_a"] == 0
    assert response.factors["signal_weights"]["unknown_b"] == 0


def test_known_signal_weight_unchanged():
    response = _decision(
        RiskRequest(signals=["waf_block", "invented_future_signal"]),
        {"risk_multiplier": 1.0, "signal_count": 0},
    )
    assert response.factors["signal_weights"]["waf_block"] == 30
    assert response.factors["signal_weights"]["invented_future_signal"] == 0
    assert response.factors["raw_score"] == 30.0
