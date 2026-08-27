from math import isfinite


class DecisionMatrix:
    """Deterministic risk/confidence policy with no permissive fallback."""

    def get_action(self, risk_score: float, confidence: float) -> str:
        if not isfinite(risk_score) or not isfinite(confidence):
            return "BLOCK"

        risk = min(100.0, max(0.0, risk_score))
        confidence_level = "low" if confidence < 0.4 else "medium" if confidence < 0.7 else "high"

        if risk < 30:
            return "ALLOW"
        if risk < 60:
            return "CHALLENGE" if confidence_level == "high" else "MONITOR"
        if confidence_level == "high":
            return "BLOCK"
        if confidence_level == "medium":
            return "CHALLENGE"
        return "MONITOR"

    def get_all_actions(self) -> list[str]:
        return ["ALLOW", "MONITOR", "CHALLENGE", "BLOCK"]
