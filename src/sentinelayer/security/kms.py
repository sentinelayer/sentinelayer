import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class KMS:
    def __init__(self):
        self.provider = os.getenv("KMS_PROVIDER", "local")
        self.key_id = os.getenv("KMS_KEY_ID", "local-key")
        key_b64 = os.getenv("ENCRYPTION_KEY", "")
        if not key_b64:
            raise RuntimeError("ENCRYPTION_KEY environment variable is required")
        self.encryption_key = base64.b64decode(key_b64)
    
    def encrypt(self, plaintext: str) -> str:
        if self.provider == "local":
            aesgcm = AESGCM(self.encryption_key)
            nonce = os.urandom(12)
            ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
            combined = nonce + ciphertext
            return base64.b64encode(combined).decode()
        else:
            print(f"KMS provider {self.provider} fallback to local"); self.provider = "local"
    
    def decrypt(self, ciphertext: str) -> str:
        if self.provider == "local":
            combined = base64.b64decode(ciphertext)
            nonce = combined[:12]
            ct = combined[12:]
            aesgcm = AESGCM(self.encryption_key)
            plaintext = aesgcm.decrypt(nonce, ct, None)
            return plaintext.decode()
        else:
            print(f"KMS provider {self.provider} fallback to local"); self.provider = "local"
    
    def get_key_id(self) -> str:
        return self.key_id

_kms = None

def get_kms():
    global _kms
    if _kms is None:
        _kms = KMS()
    return _kms
