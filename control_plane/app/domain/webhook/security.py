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
        if not isinstance(signature, str) or len(signature) != 64:
            return False
        return hmac.compare_digest(expected, signature)

    MAX_RECENT_IDENTIFIERS = 10_000

    def _remember(self, cache: dict, identifier: str, *, cleanup) -> bool:
        # This is a bounded process-local helper, NOT a distributed replay
        # protection mechanism. Never evict a fresh key to make capacity.
        if (not isinstance(identifier, str) or not 1 <= len(identifier) <= 256
                or any(ord(char) < 33 or ord(char) > 126 for char in identifier)):
            return False
        cleanup()
        if identifier in cache or len(cache) >= self.MAX_RECENT_IDENTIFIERS:
            return False
        cache[identifier] = datetime.utcnow().isoformat()
        return True

    def verify_nonce(self, nonce: str) -> bool:
        return self._remember(self.nonce_cache, nonce, cleanup=self._cleanup_nonce_cache)

    def verify_replay(self, request_id: str) -> bool:
        return self._remember(self.replay_cache, request_id, cleanup=self._cleanup_replay_cache)

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
