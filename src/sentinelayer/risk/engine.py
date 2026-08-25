import time
import math
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

@dataclass
class RiskSignal:
    name: str
    score: float
    weight: float = 1.0
    confidence: float = 0.5
    source: str = ""
    timestamp: float = field(default_factory=time.time)
    details: Dict[str, Any] = field(default_factory=dict)

class RiskEngine:
    def __init__(self):
        self.signals: List[RiskSignal] = []
        self.risk_thresholds = {
            "low": 30,
            "medium": 50,
            "high": 70,
            "critical": 85
        }
        self.signal_weights = {
            "waf_block": 1.5,
            "anomaly_detection": 1.0,
            "rate_limit": 1.2,
            "auth_failure": 0.8,
            "sequence_detection": 1.4,
            "correlation": 1.3,
        }
    
    def add_signal(self, name: str, score: float, source: str = "", details: Dict[str, Any] = None) -> None:
        weight = self.signal_weights.get(name, 1.0)
        confidence = min(1.0, max(0.0, score * 0.8 + 0.2))
        
        if not isinstance(score, (int, float)) or math.isnan(score) or math.isinf(score):
            score = 0.0
        score = max(0.0, min(100.0, score))
        
        signal = RiskSignal(
            name=name,
            score=score,
            weight=weight,
            confidence=confidence,
            source=source,
            details=details or {}
        )
        self.signals.append(signal)
    
    def calculate_risk(self, signals: Optional[List[RiskSignal]] = None) -> Dict[str, Any]:
        if signals is None:
            signals = self.signals
        
        if not signals:
            return {
                "score": 0,
                "level": "none",
                "confidence": 0.0,
                "signals": [],
                "decision": "allow"
            }
        
        total_weighted_score = 0.0
        total_weight = 0.0
        confidence_sum = 0.0
        
        for signal in signals:
            if not isinstance(signal.score, (int, float)) or math.isnan(signal.score) or math.isinf(signal.score):
                continue
            
            score = max(0.0, min(100.0, signal.score))
            weight = self.signal_weights.get(signal.name, 1.0)
            confidence = signal.confidence
            
            if not isinstance(confidence, (int, float)) or math.isnan(confidence) or math.isinf(confidence):
                confidence = 0.5
            confidence = max(0.0, min(1.0, confidence))
            
            total_weighted_score += score * weight
            total_weight += weight
            confidence_sum += confidence
        
        if total_weight == 0:
            return {
                "score": 0,
                "level": "none",
                "confidence": 0.0,
                "signals": [],
                "decision": "allow"
            }
        
        avg_score = max(0.0, min(100.0, total_weighted_score / total_weight))
        avg_confidence = confidence_sum / len(signals) if signals else 0.0
        
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
                    "source": s.source
                }
                for s in signals
            ],
            "signal_count": len(signals)
        }
    
    def clear_signals(self) -> None:
        self.signals = []

def get_risk_engine() -> RiskEngine:
    return RiskEngine()
_risk_engine = None

def get_risk_engine():
    global _risk_engine
    if _risk_engine is None:
        _risk_engine = RiskEngine()
    return _risk_engine
