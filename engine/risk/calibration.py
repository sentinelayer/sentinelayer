class Calibration:
    def __init__(self):
        self.calibration_factor = 1.0

    def calibrate(self, raw_score: float) -> float:
        return min(100, max(0, raw_score * self.calibration_factor))

    def set_factor(self, factor: float):
        self.calibration_factor = factor

    def get_factor(self) -> float:
        return self.calibration_factor
