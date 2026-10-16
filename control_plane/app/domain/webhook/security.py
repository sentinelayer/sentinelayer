import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone


class WebhookSecurity:
    """Local signature/replay helper, not a distributed replay store.

    The webhook worker uses per-registration KMS-protected secrets and durable
    payment/event tables instead. In-memory replay state must not be relied on
    across application replicas.
    """

    def __init__(self, secret: str | None = None):
        configured = secret if secret is not None else os.getenv("WEBHOOK_SECRET")
        if not configured or len(configured.encode("utf-8")) < 32:
            raise ValueError("WEBHOOK_SECRET_REQUIRED")
        self.secret = configured
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
        if ttl_seconds <= 0:
            return True
        try:
            ts = datetime.fromisoformat(timestamp)
            if ts.tzinfo is None:
                return True
            age = datetime.now(timezone.utc) - ts
            return age < timedelta(0) or age > timedelta(seconds=ttl_seconds)
        except (TypeError, ValueError, OverflowError):
            return True
