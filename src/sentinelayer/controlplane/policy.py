import os
import hashlib
import hmac
import json

class PolicyManager:
    def __init__(self):
        self.secret = os.getenv("POLICY_SIGNING_SECRET")
        if not self.secret:
            raise ValueError("POLICY_SIGNING_SECRET is required")
        self.policies = {}
    
    def create_policy(self, policy_id: str, rules: dict) -> dict:
        policy = {
            "id": policy_id,
            "rules": rules,
            "signature": self._sign_policy(rules)
        }
        self.policies[policy_id] = policy
        return policy
    
    def _sign_policy(self, rules: dict) -> str:
        data = json.dumps(rules, sort_keys=True)
        return hmac.new(self.secret.encode(), data.encode(), hashlib.sha256).hexdigest()

policy_manager = PolicyManager()
