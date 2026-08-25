import os
import base64
import hashlib
from typing import Optional

class KMS:
    def __init__(self):
        self.provider = os.getenv("KMS_PROVIDER", "local")
        self.key_id = os.getenv("KMS_KEY_ID", "local-key")
        self.encryption_key = os.getenv("ENCRYPTION_KEY", "")
    
    def encrypt(self, plaintext: str) -> str:
        if self.provider == "local":
            if not self.encryption_key:
                self.encryption_key = base64.b64encode(os.urandom(32)).decode()
            key_bytes = base64.b64decode(self.encryption_key)
            plaintext_bytes = plaintext.encode()
            encrypted = bytes(a ^ b for a, b in zip(plaintext_bytes, key_bytes[:len(plaintext_bytes)]))
            return base64.b64encode(encrypted).decode()
        else:
            raise NotImplementedError(f"KMS provider {self.provider} not implemented")
    
    def decrypt(self, ciphertext: str) -> str:
        if self.provider == "local":
            if not self.encryption_key:
                raise ValueError("Encryption key not set")
            key_bytes = base64.b64decode(self.encryption_key)
            ciphertext_bytes = base64.b64decode(ciphertext)
            decrypted = bytes(a ^ b for a, b in zip(ciphertext_bytes, key_bytes[:len(ciphertext_bytes)]))
            return decrypted.decode()
        else:
            raise NotImplementedError(f"KMS provider {self.provider} not implemented")
    
    def get_key_id(self) -> str:
        return self.key_id

_kms = None

def get_kms():
    global _kms
    if _kms is None:
        _kms = KMS()
    return _kms
