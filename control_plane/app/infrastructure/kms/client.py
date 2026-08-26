import logging
import os

from cryptography.fernet import Fernet

log = logging.getLogger(__name__)


class KMSClient:
    def __init__(self) -> None:
        raw = os.getenv("KMS_KEY")
        env = os.getenv("SL_ENV", "development")
        if not raw:
            if env in ("production", "prod"):
                raise RuntimeError("KMS_KEY required in production")
            raw = Fernet.generate_key().decode()
            log.warning("KMS_KEY unset — generated ephemeral key (dev only)")
        self.key = raw.encode() if isinstance(raw, str) else raw
        self.fernet = Fernet(self.key)

    def encrypt(self, data: str) -> str:
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, data: str) -> str:
        return self.fernet.decrypt(data.encode()).decode()

    def rotate_key(self) -> dict:
        new_key = Fernet.generate_key()
        self.key = new_key
        self.fernet = Fernet(self.key)
        return {"status": "rotated", "note": "persist new key to KMS_KEY / secret store"}
