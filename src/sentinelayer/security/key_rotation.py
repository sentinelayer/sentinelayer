import os
import time
import secrets
import redis
import json
import threading
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class KeyEntry:
    key_id: str
    key_value: str
    created_at: float
    expires_at: float
    is_active: bool = True
    rotated_by: str = "system"

class KeyRotation:
    def __init__(self):
        self.rotation_interval = 1
        self.redis_client = None
        self._init_redis()
        self.current_key_id = None
        self.load_keys()
        self.start_auto_rotation()
    
    def _init_redis(self):
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("Key rotation: Redis connected")
        except Exception as e:
            logger.warning(f"Key rotation: Redis not available ({e}), using in-memory only")
            self.redis_client = None
    
    def _get_key(self, key_id: str) -> Optional[Dict]:
        if self.redis_client:
            data = self.redis_client.get(f"key:{key_id}")
            if data:
                return json.loads(data)
        return None
    
    def _set_key(self, key_id: str, data: Dict):
        if self.redis_client:
            self.redis_client.setex(f"key:{key_id}", 86400 * 30, json.dumps(data))
            self.redis_client.set("key:current", key_id)
    
    def _get_current_key_id(self) -> Optional[str]:
        if self.redis_client:
            return self.redis_client.get("key:current")
        return self.current_key_id
    
    def load_keys(self):
        if self.redis_client:
            current = self._get_current_key_id()
            if current:
                self.current_key_id = current
    
    def generate_key(self, length: int = 32) -> str:
        return secrets.token_urlsafe(length)
    
    def create_key(self, key_id: str, rotated_by: str = "system") -> KeyEntry:
        key_value = self.generate_key()
        now = time.time()
        entry = {
            "key_id": key_id,
            "key_value": key_value,
            "created_at": now,
            "expires_at": now + (self.rotation_interval * 86400),
            "is_active": True,
            "rotated_by": rotated_by
        }
        self._set_key(key_id, entry)
        self.current_key_id = key_id
        logger.info(f"Key created: {key_id}")
        return KeyEntry(**entry)
    
    def rotate_key(self, key_id: str, rotated_by: str = "system") -> Optional[KeyEntry]:
        old = self._get_key(key_id)
        if old:
            old["is_active"] = False
            self._set_key(key_id, old)
        new_key_id = f"{key_id}_{int(time.time())}"
        return self.create_key(new_key_id, rotated_by)
    
    def get_current_key(self) -> Optional[KeyEntry]:
        key_id = self._get_current_key_id()
        if key_id:
            data = self._get_key(key_id)
            if data:
                return KeyEntry(**data)
        return None
    
    def check_and_rotate(self) -> Optional[KeyEntry]:
        current = self.get_current_key()
        if current and time.time() > current.expires_at:
            logger.info(f"Key {current.key_id} expired, rotating...")
            return self.rotate_key(current.key_id, "auto_rotation")
        return current
    
    def start_auto_rotation(self):
        def rotate_loop():
            while True:
                time.sleep(3600)
                self.check_and_rotate()
        thread = threading.Thread(target=rotate_loop, daemon=True)
        thread.start()
    
    def get_stats(self) -> Dict[str, Any]:
        current = self.get_current_key()
        return {
            "current_key_id": self.current_key_id,
            "rotation_interval_days": self.rotation_interval,
            "redis_available": self.redis_client is not None,
            "key_active": current is not None
        }

_key_rotation = None

def get_key_rotation():
    global _key_rotation
    if _key_rotation is None:
        _key_rotation = KeyRotation()
    return _key_rotation
