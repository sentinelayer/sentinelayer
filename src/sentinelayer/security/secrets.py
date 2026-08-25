import os
import json
from typing import Optional
from sentinelayer.security.kms import get_kms

class SecretsManager:
    def __init__(self, secrets_file: str = "private/secrets.json"):
        self.secrets_file = secrets_file
        self.kms = get_kms()
        self.secrets = self.load_secrets()
    
    def load_secrets(self) -> dict:
        try:
            with open(self.secrets_file, "r") as f:
                data = json.load(f)
                for key, value in data.items():
                    if isinstance(value, str) and value.startswith("encrypted:"):
                        try:
                            data[key] = self.kms.decrypt(value.replace("encrypted:", ""))
                        except:
                            pass
                return data
        except:
            return {}
    
    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        if key in self.secrets:
            return self.secrets[key]
        return os.getenv(key, default)
    
    def set_secret(self, key: str, value: str) -> None:
        encrypted = self.kms.encrypt(value)
        self.secrets[key] = encrypted
        self.save_secrets()
    
    def save_secrets(self) -> None:
        os.makedirs("private", exist_ok=True)
        with open(self.secrets_file, "w") as f:
            json.dump(self.secrets, f, indent=2)

def get_secrets_manager() -> SecretsManager:
    return SecretsManager()
_secrets_manager = None

def get_secrets_manager():
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager
