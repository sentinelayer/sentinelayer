import hmac
import hashlib
import time
import secrets
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class WebhookConfig:
    id: str
    url: str
    secret: str
    events: list
    retries: int = 3

class WebhookSecurity:
    def __init__(self):
        self.configs: Dict[str, WebhookConfig] = {}
        self.nonce_store: Dict[str, float] = {}
        self.nonce_ttl = 300
    
    def create_config(self, url: str, events: list) -> WebhookConfig:
        config_id = f"wh_{len(self.configs) + 1}"
        secret = secrets.token_urlsafe(32)
        config = WebhookConfig(config_id, url, secret, events)
        self.configs[config_id] = config
        return config
    
    def verify_signature(self, payload: str, signature: str, secret: str) -> bool:
        expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, expected)
    
    def verify_nonce(self, nonce: str) -> bool:
        if nonce in self.nonce_store:
            if time.time() - self.nonce_store[nonce] < self.nonce_ttl:
                return False
        self.nonce_store[nonce] = time.time()
        return True
    
    def get_config(self, config_id: str) -> Optional[WebhookConfig]:
        return self.configs.get(config_id)

_webhook_security = None

def get_webhook_security():
    global _webhook_security
    if _webhook_security is None:
        _webhook_security = WebhookSecurity()
    return _webhook_security
