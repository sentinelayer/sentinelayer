class RiskNormalization:
    @staticmethod
    def normalize(score: float) -> float:
        return min(100, max(0, score))

    @staticmethod
    def normalize_signal(signal_value: float, min_val: float = 0, max_val: float = 100) -> float:
        if max_val == min_val:
            return 0.5
        return (signal_value - min_val) / (max_val - min_val)

    @staticmethod
    def combine_scores(scores: list) -> float:
        if not scores:
            return 0.0
        return sum(scores) / len(scores)
