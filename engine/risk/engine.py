from typing import Dict, List
from src.sentinelayer.risk.correlation import correlator

class RiskEngine:
    def __init__(self):
        self.thresholds = {
            "allow": 30,
            "monitor": 60,
            "challenge": 80,
            "block": 85
        }
        self.confidence_threshold = 0.7
        self.calibration_factor = 1.0

    def calculate(self, context: Dict) -> float:
        score = 0
        confidence = 0.5

        failed_attempts = context.get("failed_attempts", 0)
        if failed_attempts > 3:
            score += min(30, failed_attempts * 5)
            confidence += 0.1

        if context.get("suspicious_ip", False):
            score += 25
            confidence += 0.15

        if context.get("unusual_time", False):
            score += 15
            confidence += 0.1

        if context.get("multiple_tenants", False):
            score += 20
            confidence += 0.15

        correlation_result = correlator.correlate(context)
        if correlation_result.get("risk_multiplier", 1.0) > 1:
            score = score * correlation_result["risk_multiplier"]
            confidence = min(1.0, confidence + 0.2)

        score = min(100, max(0, score))
        confidence = min(1.0, max(0, confidence))

        return {
            "score": round(score, 1),
            "confidence": round(confidence, 2),
            "action": self.get_action(score),
            "factors": {
                "failed_attempts": failed_attempts,
                "suspicious_ip": context.get("suspicious_ip", False),
                "unusual_time": context.get("unusual_time", False),
                "multiple_tenants": context.get("multiple_tenants", False)
            }
        }

    def get_action(self, score: float) -> str:
        if score >= 80:
            return "BLOCK"
        elif score >= 60:
            return "CHALLENGE"
        elif score >= 30:
            return "MONITOR"
        else:
            return "ALLOW"

risk_engine = RiskEngine()
