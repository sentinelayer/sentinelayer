from datetime import datetime


class DecisionReplay:
    def __init__(self):
        self.history = []

    def record(self, decision: dict):
        self.history.append({
            "decision": decision,
            "timestamp": datetime.utcnow().isoformat()
        })

    def replay(self, context: dict) -> list:
        results = []
        for entry in self.history:
            if self._matches(entry["decision"], context):
                results.append(entry)
        return results

    def counterfactual(self, context: dict, changed: dict) -> dict:
        original = self.replay(context)
        if not original:
            return {"error": "No matching decisions found"}
        last = original[-1]["decision"]
        return {
            "original": last,
            "counterfactual": {
                "risk_score": min(100, last.get("risk_score", 0) + changed.get("delta", 20)),
                "action": "BLOCK" if last.get("risk_score", 0) + changed.get("delta", 20) >= 80 else "ALLOW"
            }
        }

    def _matches(self, decision: dict, context: dict) -> bool:
        return decision.get("tenant_id") == context.get("tenant_id")
