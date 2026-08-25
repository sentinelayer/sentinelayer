from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import time
import json

@dataclass
class Decision:
    action: str  # allow, block, challenge, monitor
    risk_level: str
    risk_score: float
    confidence: float
    reason: str = ""
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    rollback_plan: Optional[Dict[str, Any]] = None

class DecisionSafetyLayer:
    """Decision layer with kill switch and rollback"""
    
    def __init__(self):
        self.decisions: Dict[str, Decision] = {}  # request_id -> Decision
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
        """Make a decision based on risk result"""
        
        # If kill switch is active, block everything
        if self.kill_switch_active:
            return Decision(
                action="block",
                risk_level="critical",
                risk_score=1.0,
                confidence=1.0,
                reason="Kill switch active",
                metadata={"kill_switch": True}
            )
        
        # Get decision from risk
        risk_decision = risk_result.get("decision", "allow")
        risk_level = risk_result.get("level", "none")
        risk_score = risk_result.get("score", 0.0)
        confidence = risk_result.get("confidence", 0.0)
        
        # Override based on critical signals
        signals = risk_result.get("signals", [])
        for signal in signals:
            if signal.get("name") == "waf_block" and signal.get("score") > 0.8:
                risk_decision = "block"
                break
            if signal.get("name") == "threat_intel" and signal.get("score") > 0.9:
                risk_decision = "block"
                break
        
        # Create decision
        decision = Decision(
            action=risk_decision,
            risk_level=risk_level,
            risk_score=risk_score,
            confidence=confidence,
            reason=f"Risk level: {risk_level}, decision: {risk_decision}",
            metadata=context or {}
        )
        
        # Store decision
        self.decisions[request_id] = decision
        
        # Keep history
        self.last_decisions.append(decision)
        if len(self.last_decisions) > self.max_history:
            self.last_decisions.pop(0)
        
        return decision
    
    def activate_kill_switch(self, reason: str = "") -> None:
        """Activate kill switch - block all requests"""
        self.kill_switch_active = True
        self.add_to_rollback_stack({
            "action": "kill_switch_activated",
            "reason": reason,
            "timestamp": time.time()
        })
    
    def deactivate_kill_switch(self) -> None:
        """Deactivate kill switch"""
        self.kill_switch_active = False
    
    def get_decision(self, request_id: str) -> Optional[Decision]:
        """Get decision by request ID"""
        return self.decisions.get(request_id)
    
    def add_to_rollback_stack(self, entry: Dict[str, Any]) -> None:
        """Add entry to rollback stack"""
        self.rollback_stack.append(entry)
        # Keep only last 100
        if len(self.rollback_stack) > 100:
            self.rollback_stack.pop(0)
    
    def get_rollback_plan(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get rollback plan for a request"""
        decision = self.decisions.get(request_id)
        if decision and decision.rollback_plan:
            return decision.rollback_plan
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        total_decisions = len(self.last_decisions)
        if total_decisions == 0:
            return {
                "total_decisions": 0,
                "blocked": 0,
                "allowed": 0,
                "kill_switch_active": self.kill_switch_active
            }
        
        blocked = sum(1 for d in self.last_decisions if d.action == "block")
        
        return {
            "total_decisions": total_decisions,
            "blocked": blocked,
            "blocked_percent": (blocked / total_decisions) * 100 if total_decisions > 0 else 0,
            "allowed": total_decisions - blocked,
            "kill_switch_active": self.kill_switch_active,
            "rollback_stack_size": len(self.rollback_stack)
        }

def get_decision_safety() -> DecisionSafetyLayer:
    return DecisionSafetyLayer()
from sentinelayer.decision.counterfactual import get_counterfactual_engine

class DecisionSafetyLayer:
    def __init__(self):
        self.decisions: Dict[str, Decision] = {}
        self.kill_switch_active = False
        self.rollback_stack: List[Dict[str, Any]] = []
        self.last_decisions: List[Decision] = []
        self.max_history = 100
        self.counterfactual = get_counterfactual_engine()
    
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
        
        counterfactuals = self.counterfactual.generate(risk_result)
        
        risk_decision = risk_result.get("decision", "allow")
        risk_level = risk_result.get("level", "none")
        risk_score = risk_result.get("score", 0.0)
        confidence = risk_result.get("confidence", 0.0)
        
        signals = risk_result.get("signals", [])
        for signal in signals:
            if signal.get("name") == "waf_block" and signal.get("score") > 0.8:
                risk_decision = "block"
                break
            if signal.get("name") == "sequence_detection" and signal.get("score") > 0.8:
                risk_decision = "block"
                break
        
        decision = Decision(
            action=risk_decision,
            risk_level=risk_level,
            risk_score=risk_score,
            confidence=confidence,
            reason=f"Risk level: {risk_level}, decision: {risk_decision}",
            metadata={
                "context": context or {},
                "counterfactuals": [
                    {
                        "original": c.original_decision,
                        "alternative": c.alternative_decision,
                        "reasoning": c.reasoning
                    }
                    for c in counterfactuals[:3]
                ]
            }
        )
        
        self.decisions[request_id] = decision
        self.last_decisions.append(decision)
        if len(self.last_decisions) > self.max_history:
            self.last_decisions.pop(0)
        
        return decision
    
    def get_counterfactual_history(self):
        return self.counterfactual.get_history()
