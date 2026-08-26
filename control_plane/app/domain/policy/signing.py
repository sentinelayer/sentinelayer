import hmac
import hashlib
import json
import os

class PolicySigning:
    def __init__(self):
        self.secret = os.getenv("POLICY_SIGNING_SECRET", "change-me")

    def sign(self, policy: dict) -> str:
        data = json.dumps(policy, sort_keys=True)
        return hmac.new(self.secret.encode(), data.encode(), hashlib.sha256).hexdigest()

    def verify(self, policy: dict, signature: str) -> bool:
        expected = self.sign(policy)
        return hmac.compare_digest(expected, signature)
