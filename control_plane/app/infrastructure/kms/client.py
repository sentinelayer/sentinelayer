import os
from cryptography.fernet import Fernet

class KMSClient:
    def __init__(self):
        self.key = os.getenv("KMS_KEY", Fernet.generate_key())
        self.fernet = Fernet(self.key if isinstance(self.key, bytes) else self.key.encode())

    def encrypt(self, data: str) -> str:
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, data: str) -> str:
        return self.fernet.decrypt(data.encode()).decode()

    def rotate_key(self):
        self.key = Fernet.generate_key()
        self.fernet = Fernet(self.key)
        return {"new_key": self.key.decode()}
