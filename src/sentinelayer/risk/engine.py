from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import time

@dataclass
class RiskSignal:
    name: str
    score: float  # 0-1
    weight: float = 1.0
    confidence: float = 0.5
    source: str = ""
    timestamp: float = field(default_factory=time.time)
    details: Dict[str, Any] = field(default_factory=dict)

class RiskEngine:
    """Risk scoring engine with confidence calculation"""
    
    def __init__(self):
        self.signals: List[RiskSignal] = []
        self.risk_thresholds = {
            "low": 0.3,
            "medium": 0.5,
            "high": 0.7,
            "critical": 0.85
        }
        self.signal_weights = {
            "waf_block": 1.5,
            "anomaly_detection": 1.0,
            "rate_limit": 1.2,
            "auth_failure": 0.8,
            "business_flow": 1.3,
            "threat_intel": 1.4,
        }
    
    def add_signal(self, name: str, score: float, source: str = "", details: Dict[str, Any] = None) -> None:
        """Add a risk signal to the engine"""
        weight = self.signal_weights.get(name, 1.0)
        confidence = min(1.0, score * 0.8 + 0.2)  # Simple confidence proxy
        
        signal = RiskSignal(
            name=name,
            score=score,
            weight=weight,
            confidence=confidence,
            source=source,
            details=details or {}
        )
        self.signals.append(signal)
    
    def calculate_risk(self) -> Dict[str, Any]:
        """Calculate overall risk score"""
        if not self.signals:
            return {
                "score": 0.0,
                "level": "none",
                "confidence": 0.0,
                "signals": [],
                "decision": "allow"
            }
        
        total_weighted_score = 0.0
        total_weight = 0.0
        confidence_sum = 0.0
        
        for signal in self.signals:
            weighted = signal.score * signal.weight
            total_weighted_score += weighted
            total_weight += signal.weight
            confidence_sum += signal.confidence
        
        avg_score = total_weighted_score / total_weight if total_weight > 0 else 0
        avg_confidence = confidence_sum / len(self.signals) if self.signals else 0
        
        # Determine risk level
        if avg_score >= self.risk_thresholds["critical"]:
            level = "critical"
            decision = "block"
        elif avg_score >= self.risk_thresholds["high"]:
            level = "high"
            decision = "block"
        elif avg_score >= self.risk_thresholds["medium"]:
            level = "medium"
            decision = "challenge"
        elif avg_score >= self.risk_thresholds["low"]:
            level = "low"
            decision = "monitor"
        else:
            level = "none"
            decision = "allow"
        
        return {
            "score": avg_score,
            "level": level,
            "confidence": avg_confidence,
            "decision": decision,
            "signals": [
                {
                    "name": s.name,
                    "score": s.score,
                    "weight": s.weight,
                    "confidence": s.confidence,
                    "source": s.source,
                    "details": s.details
                }
                for s in self.signals
            ],
            "signal_count": len(self.signals)
        }
    
    def clear_signals(self) -> None:
        """Clear all signals"""
        self.signals = []

def get_risk_engine() -> RiskEngine:
    return RiskEngine()
