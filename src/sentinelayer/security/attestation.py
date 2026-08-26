import hashlib
import json
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

class Attestation:
    def __init__(self):
        self.private_key = None
        self.public_key = None
        self.load_keys()
    
    def load_keys(self):
        if os.path.exists("private/attestation_private.pem"):
            with open("private/attestation_private.pem", "rb") as f:
                self.private_key = rsa.load_pem_private_key(f.read(), password=None)
        if os.path.exists("private/attestation_public.pem"):
            with open("private/attestation_public.pem", "rb") as f:
                self.public_key = rsa.load_pem_public_key(f.read())
    
    def sign(self, data: bytes) -> bytes:
        if not self.private_key:
            raise RuntimeError("Private key not loaded")
        return self.private_key.sign(data, padding.PKCS1v15(), hashes.SHA256())
    
    def verify(self, data: bytes, signature: bytes) -> bool:
        if not self.public_key:
            raise RuntimeError("Public key not loaded")
        try:
            self.public_key.verify(signature, data, padding.PKCS1v15(), hashes.SHA256())
            return True
        except:
            return False

attestation = Attestation()
