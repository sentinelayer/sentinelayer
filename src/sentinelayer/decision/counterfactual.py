import time
import copy
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

@dataclass
class CounterfactualResult:
    original_decision: str
    alternative_decision: str
    score_diff: float
    reasoning: str
    timestamp: float
    variables_changed: List[str]

class CounterfactualEngine:
    def __init__(self):
        self.history: List[CounterfactualResult] = []
        self.max_history = 100
    
    def generate(self, risk_result: Dict[str, Any]) -> List[CounterfactualResult]:
        results = []
        original_score = risk_result.get("score", 0)
        original_decision = risk_result.get("decision", "allow")
        signals = risk_result.get("signals", [])
        
        if not signals:
            return results
        
        for i, signal in enumerate(signals):
            test_signals = copy.deepcopy(signals)
            test_signals[i]["score"] = signal["score"] * 0.5
            
            test_risk = {
                "score": original_score * 0.7,
                "level": self._get_level(original_score * 0.7),
                "decision": self._get_decision(original_score * 0.7),
                "signals": test_signals,
                "confidence": risk_result.get("confidence", 0.5)
            }
            
            if test_risk["decision"] != original_decision:
                results.append(CounterfactualResult(
                    original_decision=original_decision,
                    alternative_decision=test_risk["decision"],
                    score_diff=original_score - test_risk["score"],
                    reasoning=f"Reducing signal '{signal['name']}' by 50% would change decision from {original_decision} to {test_risk['decision']}",
                    timestamp=time.time(),
                    variables_changed=[signal["name"]]
                ))
        
        self.history.extend(results)
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
        return results
    
    def _get_level(self, score: float) -> str:
        if score >= 85:
            return "critical"
        elif score >= 70:
            return "high"
        elif score >= 50:
            return "medium"
        elif score >= 30:
            return "low"
        return "none"
    
    def _get_decision(self, score: float) -> str:
        if score >= 70:
            return "block"
        elif score >= 50:
            return "challenge"
        elif score >= 30:
            return "monitor"
        return "allow"
    
    def get_history(self, limit: int = 20) -> List[CounterfactualResult]:
        return self.history[-limit:]

_counterfactual = None

def get_counterfactual_engine():
    global _counterfactual
    if _counterfactual is None:
        _counterfactual = CounterfactualEngine()
    return _counterfactual
