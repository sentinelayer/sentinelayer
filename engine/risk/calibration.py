"""Finite bounded calibration factors for security decisions."""

import math


class Calibration:
    def __init__(self):
        self.calibration_factor = 1.0

    def calibrate(self, raw_score: float) -> float:
        if type(raw_score) not in (int, float) or not math.isfinite(raw_score):
            raise ValueError("INVALID_RAW_RISK_SCORE")
        if not math.isfinite(self.calibration_factor) or self.calibration_factor <= 0:
            raise ValueError("INVALID_CALIBRATION_FACTOR")
        return min(100.0, max(0.0, raw_score * self.calibration_factor))

    def set_factor(self, factor: float):
        if type(factor) not in (int, float) or not math.isfinite(factor) or factor <= 0:
            raise ValueError("INVALID_CALIBRATION_FACTOR")
        self.calibration_factor = float(factor)

    def get_factor(self) -> float:
        return self.calibration_factor
