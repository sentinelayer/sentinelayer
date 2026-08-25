import os
import base64
from typing import Optional

class SecretsManager:
    """Secrets manager - baca dari environment variable, bukan plaintext file"""
    
    def __init__(self):
        # Semua secret dari environment variable
        self.jwt_secret = os.getenv("JWT_SECRET_KEY", "")
        self.encryption_key = os.getenv("ENCRYPTION_KEY", "")
        self.database_url = os.getenv("DATABASE_URL", "")
        self.redis_url = os.getenv("REDIS_URL", "")
    
    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret from environment"""
        return os.getenv(key, default)
    
    def get_jwt_secret(self) -> str:
        if not self.jwt_secret:
            raise ValueError("JWT_SECRET_KEY not set in environment")
        return self.jwt_secret
    
    def get_encryption_key(self) -> str:
        if not self.encryption_key:
            # Generate fallback (tapi sebaiknya di-set di env)
            return base64.b64encode(os.urandom(32)).decode()
        return self.encryption_key

def get_secrets_manager() -> SecretsManager:
    return SecretsManager()
