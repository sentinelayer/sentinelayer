import json
import hashlib
import hmac
import os
from datetime import datetime
from typing import Dict, List

class PolicyManager:
    def __init__(self):
        self.policies = {}
        self.versions = {}
        self.secret = os.getenv("POLICY_SIGNING_SECRET", "change-me")
    
    def create_policy(self, policy_id: str, rules: Dict) -> Dict:
        version = len(self.versions.get(policy_id, [])) + 1
        policy = {
            "id": policy_id,
            "rules": rules,
            "version": version,
            "created_at": datetime.utcnow().isoformat(),
            "signature": self._sign_policy(rules)
        }
        
        if policy_id not in self.versions:
            self.versions[policy_id] = []
        self.versions[policy_id].append(policy)
        self.policies[policy_id] = policy
        return policy
    
    def get_policy(self, policy_id: str, version: int = None) -> Dict:
        if version is None:
            return self.policies.get(policy_id)
        
        versions = self.versions.get(policy_id, [])
        if version <= len(versions):
            return versions[version - 1]
        return None
    
    def rollback(self, policy_id: str, version: int) -> Dict:
        policy = self.get_policy(policy_id, version)
        if policy:
            self.policies[policy_id] = policy
            return policy
        return None
    
    def _sign_policy(self, rules: Dict) -> str:
        data = json.dumps(rules, sort_keys=True)
        return hmac.new(
            self.secret.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def verify_policy(self, policy: Dict) -> bool:
        expected = self._sign_policy(policy["rules"])
        return hmac.compare_digest(expected, policy["signature"])

policy_manager = PolicyManager()
