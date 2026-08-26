class RiskEngine:
    def __init__(self):
        self.thresholds = {
            "allow": 30,
            "monitor": 60,
            "challenge": 80,
            "block": 85
        }
    
    def calculate(self, context: dict) -> float:
        # Simple risk calculation
        score = 0
        if context.get("failed_attempts", 0) > 3:
            score += 30
        if context.get("suspicious_ip", False):
            score += 25
        if context.get("unusual_time", False):
            score += 15
        if context.get("multiple_tenants", False):
            score += 20
        return min(score, 100)
    
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
