class DecisionMatrix:
    def __init__(self):
        self.matrix = [
            {"risk": [0, 30], "confidence": [0.7, 1.0], "action": "ALLOW"},
            {"risk": [30, 60], "confidence": [0.5, 0.7], "action": "MONITOR"},
            {"risk": [60, 80], "confidence": [0.3, 0.7], "action": "CHALLENGE"},
            {"risk": [80, 100], "confidence": [0.0, 1.0], "action": "BLOCK"},
        ]

    def get_action(self, risk_score: float, confidence: float) -> str:
        for entry in self.matrix:
            risk_min, risk_max = entry["risk"]
            conf_min, conf_max = entry["confidence"]
            if risk_min <= risk_score <= risk_max and conf_min <= confidence <= conf_max:
                return entry["action"]
        return "ALLOW"

    def get_all_actions(self) -> list:
        return [entry["action"] for entry in self.matrix]
