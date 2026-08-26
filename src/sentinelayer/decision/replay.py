from datetime import datetime, timedelta
import json
from typing import List, Dict
from src.sentinelayer.database import SessionLocal
from src.sentinelayer.database.models import Decision

class DecisionReplay:
    def __init__(self):
        self.history = []
    
    def record_decision(self, decision: Dict):
        self.history.append({
            **decision,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep only last 1000
        if len(self.history) > 1000:
            self.history = self.history[-1000:]
    
    def replay(self, context: Dict) -> List[Dict]:
        results = []
        for past_decision in self.history:
            if self._matches_context(past_decision, context):
                results.append(past_decision)
        return results
    
    def counterfactual(self, context: Dict, changed_condition: Dict) -> Dict:
        # Find decisions with similar context
        past_decisions = self.replay(context)
        if not past_decisions:
            return {"error": "No similar decisions found"}
        
        # Simulate what would happen with changed condition
        last_decision = past_decisions[-1]
        score = last_decision.get("risk_score", 0)
        
        if changed_condition.get("increase_risk"):
            score = min(100, score + 20)
        if changed_condition.get("decrease_risk"):
            score = max(0, score - 20)
        
        return {
            "original_decision": last_decision,
            "counterfactual_decision": {
                "risk_score": score,
                "action": self._get_action(score)
            }
        }
    
    def _matches_context(self, decision: Dict, context: Dict) -> bool:
        # Simple match on tenant_id and endpoint
        return (
            decision.get("tenant_id") == context.get("tenant_id") or
            decision.get("endpoint") == context.get("endpoint")
        )
    
    def _get_action(self, score: float) -> str:
        if score >= 80:
            return "BLOCK"
        elif score >= 60:
            return "CHALLENGE"
        elif score >= 30:
            return "MONITOR"
        else:
            return "ALLOW"

replay_engine = DecisionReplay()
