class RiskExplainability:
    def __init__(self):
        self.explanations = []

    def explain(self, decision: dict) -> dict:
        explanation = {
            "what": f"Decision was {decision.get('action', 'UNKNOWN')}",
            "why": decision.get('reason', 'No explanation'),
            "who": decision.get('user_id', 'system'),
            "when": decision.get('timestamp', 'now'),
            "signal": decision.get('factors', {}),
            "score": decision.get('risk_score', 0),
            "policy": decision.get('policy', 'default'),
            "version": decision.get('version', '1.0')
        }
        self.explanations.append(explanation)
        return explanation

    def get_latest(self) -> dict:
        if self.explanations:
            return self.explanations[-1]
        return {"error": "No explanations"}

    def get_all(self) -> list:
        return self.explanations
