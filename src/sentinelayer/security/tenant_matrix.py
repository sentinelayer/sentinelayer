from typing import Dict, List
from datetime import datetime, timedelta
from collections import defaultdict

class TenantAdversarialMatrix:
    def __init__(self):
        self.tenant_attacks = defaultdict(list)
        self.attack_patterns = {
            "brute_force": {"threshold": 5, "window": 60},
            "credential_stuffing": {"threshold": 3, "window": 30},
            "account_takeover": {"threshold": 2, "window": 15},
            "privilege_escalation": {"threshold": 1, "window": 5}
        }
    
    def record_attempt(self, tenant_id: str, attack_type: str, source_ip: str):
        self.tenant_attacks[tenant_id].append({
            "type": attack_type,
            "source_ip": source_ip,
            "timestamp": datetime.utcnow()
        })
        
        return self.is_under_attack(tenant_id, attack_type)
    
    def is_under_attack(self, tenant_id: str, attack_type: str) -> Dict:
        pattern = self.attack_patterns.get(attack_type)
        if not pattern:
            return {"under_attack": False}
        
        recent = [
            a for a in self.tenant_attacks[tenant_id]
            if a["type"] == attack_type
            and (datetime.utcnow() - a["timestamp"]).seconds < pattern["window"]
        ]
        
        if len(recent) >= pattern["threshold"]:
            return {
                "under_attack": True,
                "attack_type": attack_type,
                "attempts": len(recent),
                "window_seconds": pattern["window"],
                "recommended_action": self._get_action(attack_type)
            }
        
        return {"under_attack": False}
    
    def _get_action(self, attack_type: str) -> str:
        actions = {
            "brute_force": "block_ip_24h",
            "credential_stuffing": "challenge_captcha",
            "account_takeover": "require_mfa",
            "privilege_escalation": "alert_admin"
        }
        return actions.get(attack_type, "monitor")

tenant_matrix = TenantAdversarialMatrix()
