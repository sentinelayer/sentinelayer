from collections import defaultdict
from datetime import datetime, timedelta

class BusinessFlowAbuseDetector:
    def __init__(self):
        self.flows = defaultdict(list)
        self.fraud_patterns = {
            "refund_abuse": ["login", "add_payment", "coupon", "refund"],
            "credential_stuffing": ["login_failed", "login_failed", "login_failed", "login_success"],
            "data_exfil": ["download", "download", "download", "bulk_export"],
            "rate_abuse": ["api_call", "api_call", "api_call", "api_call", "api_call"]
        }

    def track(self, user_id: str, action: str, data: dict):
        self.flows[user_id].append({
            "action": action,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        })
        if len(self.flows[user_id]) > 100:
            self.flows[user_id] = self.flows[user_id][-100:]

    def detect(self, user_id: str) -> list:
        actions = [f["action"] for f in self.flows.get(user_id, [])]
        detected = []
        for pattern_name, pattern in self.fraud_patterns.items():
            if self._matches(actions, pattern):
                detected.append({
                    "pattern": pattern_name,
                    "confidence": self._calculate_confidence(actions, pattern),
                    "detected_at": datetime.utcnow().isoformat()
                })
        return detected

    def _matches(self, actions: list, pattern: list) -> bool:
        if len(actions) < len(pattern):
            return False
        return actions[-len(pattern):] == pattern

    def _calculate_confidence(self, actions: list, pattern: list) -> float:
        matches = sum(1 for i, p in enumerate(pattern) if actions[-len(pattern):][i] == p)
        return round(matches / len(pattern), 2)
