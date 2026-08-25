import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

@dataclass
class Decision:
    action: str
    risk_level: str
    risk_score: float
    confidence: float
    reason: str = ""
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    rollback_plan: Optional[Dict[str, Any]] = None

class DecisionSafetyLayer:
    def __init__(self):
        self.decisions: Dict[str, Decision] = {}
        self.kill_switch_active = False
        self.rollback_stack: List[Dict[str, Any]] = []
        self.last_decisions: List[Decision] = []
        self.max_history = 100
    
    def make_decision(
        self,
        request_id: str,
        risk_result: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> Decision:
        if self.kill_switch_active:
            return Decision(
                action="block",
                risk_level="critical",
                risk_score=1.0,
                confidence=1.0,
                reason="Kill switch active",
                metadata={"kill_switch": True}
            )
        
        risk_decision = risk_result.get("decision", "allow")
        risk_level = risk_result.get("level", "none")
        risk_score = risk_result.get("score", 0.0)
        confidence = risk_result.get("confidence", 0.0)
        
        signals = risk_result.get("signals", [])
        for signal in signals:
            if signal.get("name") == "waf_block" and signal.get("score", 0) > 70:
                risk_decision = "block"
                break
            if signal.get("name") == "sequence_detection" and signal.get("score", 0) > 70:
                risk_decision = "block"
                break
        
        decision = Decision(
            action=risk_decision,
            risk_level=risk_level,
            risk_score=risk_score,
            confidence=confidence,
            reason=f"Risk level: {risk_level}, decision: {risk_decision}",
            metadata=context or {}
        )
        
        self.decisions[request_id] = decision
        self.last_decisions.append(decision)
        if len(self.last_decisions) > self.max_history:
            self.last_decisions.pop(0)
        
        return decision
    
    def activate_kill_switch(self, reason: str = "") -> None:
        self.kill_switch_active = True
        self.rollback_stack.append({
            "action": "kill_switch_activated",
            "reason": reason,
            "timestamp": time.time()
        })
    
    def deactivate_kill_switch(self) -> None:
        self.kill_switch_active = False
    
    def get_decision(self, request_id: str) -> Optional[Decision]:
        return self.decisions.get(request_id)
    
    def get_stats(self) -> Dict[str, Any]:
        total = len(self.last_decisions)
        if total == 0:
            return {
                "total_decisions": 0,
                "blocked": 0,
                "allowed": 0,
                "kill_switch_active": self.kill_switch_active
            }
        blocked = sum(1 for d in self.last_decisions if d.action == "block")
        return {
            "total_decisions": total,
            "blocked": blocked,
            "blocked_percent": (blocked / total) * 100 if total > 0 else 0,
            "allowed": total - blocked,
            "kill_switch_active": self.kill_switch_active,
            "rollback_stack_size": len(self.rollback_stack)
        }

def get_decision_safety() -> DecisionSafetyLayer:
    return DecisionSafetyLayer()
