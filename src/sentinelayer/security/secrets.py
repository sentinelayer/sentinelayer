import os
import json
from typing import Optional

class SecretsManager:
    def __init__(self, secrets_file: str = "private/secrets.json"):
        self.secrets_file = secrets_file
        self.secrets = self.load_secrets()
    
    def load_secrets(self) -> dict:
        try:
            with open(self.secrets_file, "r") as f:
                return json.load(f)
        except:
            return {}
    
    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        if key in self.secrets:
            return self.secrets[key]
        return os.getenv(key, default)
    
    def set_secret(self, key: str, value: str) -> None:
        self.secrets[key] = value
        self.save_secrets()
    
    def save_secrets(self) -> None:
        os.makedirs("private", exist_ok=True)
        with open(self.secrets_file, "w") as f:
            json.dump(self.secrets, f, indent=2)

def get_secrets_manager() -> SecretsManager:
    return SecretsManager()
