import hmac
import hashlib
import os
from datetime import datetime, timedelta

class WebhookSecurity:
    def __init__(self):
        self.secret = os.getenv("WEBHOOK_SECRET", "change-me")
        self.nonce_cache = {}
        self.replay_cache = {}

    def generate_signature(self, payload: str) -> str:
        return hmac.new(
            self.secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

    def verify_signature(self, payload: str, signature: str) -> bool:
        expected = self.generate_signature(payload)
        return hmac.compare_digest(expected, signature)

    def verify_nonce(self, nonce: str) -> bool:
        if nonce in self.nonce_cache:
            return False
        self.nonce_cache[nonce] = datetime.utcnow().isoformat()
        self._cleanup_nonce_cache()
        return True

    def verify_replay(self, request_id: str) -> bool:
        if request_id in self.replay_cache:
            return False
        self.replay_cache[request_id] = datetime.utcnow().isoformat()
        self._cleanup_replay_cache()
        return True

    def _cleanup_nonce_cache(self):
        cutoff = datetime.utcnow() - timedelta(minutes=5)
        for nonce, timestamp in list(self.nonce_cache.items()):
            if datetime.fromisoformat(timestamp) < cutoff:
                del self.nonce_cache[nonce]

    def _cleanup_replay_cache(self):
        cutoff = datetime.utcnow() - timedelta(hours=1)
        for req_id, timestamp in list(self.replay_cache.items()):
            if datetime.fromisoformat(timestamp) < cutoff:
                del self.replay_cache[req_id]

    def is_expired(self, timestamp: str, ttl_seconds: int = 300) -> bool:
        try:
            ts = datetime.fromisoformat(timestamp)
            return datetime.utcnow() - ts > timedelta(seconds=ttl_seconds)
        except:
            return True
