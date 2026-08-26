import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature
import json

class PolicySigning:
    def __init__(self):
        self.private_key = ed25519.Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()

    def sign(self, policy: dict) -> str:
        data = json.dumps(policy, sort_keys=True).encode()
        signature = self.private_key.sign(data)
        return base64.b64encode(signature).decode()

    def verify(self, policy: dict, signature: str) -> bool:
        try:
            data = json.dumps(policy, sort_keys=True).encode()
            sig = base64.b64decode(signature)
            self.public_key.verify(sig, data)
            return True
        except InvalidSignature:
            return False

    def get_public_key(self) -> str:
        return base64.b64encode(self.public_key.public_bytes_raw()).decode()
