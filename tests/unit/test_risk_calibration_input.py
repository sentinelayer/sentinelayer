"""Reject untrustworthy risk calibration rather than emitting bogus scores."""

import pytest

from engine.risk.calibration import Calibration


@pytest.mark.parametrize("factor", [0, -1, float("inf"), float("-inf"), float("nan"), True, "1"])
def test_nonfinite_or_invalid_factor_rejected_without_mutation(factor):
    calibration = Calibration()
    with pytest.raises(ValueError, match="INVALID_CALIBRATION_FACTOR"):
        calibration.set_factor(factor)
    assert calibration.get_factor() == 1.0


@pytest.mark.parametrize("score", [float("nan"), float("inf"), float("-inf"), None, True, "100"])
def test_invalid_raw_score_rejected(score):
    with pytest.raises(ValueError, match="INVALID_RAW_RISK_SCORE"):
        Calibration().calibrate(score)


def test_finite_valid_factor_preserves_bounded_action_score():
    c = Calibration()
    c.set_factor(1.5)
    assert c.calibrate(30) == 45.0
    assert c.calibrate(100) == 100.0
    assert c.calibrate(-1) == 0.0
