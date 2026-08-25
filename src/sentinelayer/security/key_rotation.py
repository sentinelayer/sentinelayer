import os
import time
import json
import secrets
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
        self.keys: Dict[str, KeyEntry] = {}
        self.current_key_id: Optional[str] = None
        self.rotation_interval = 1  # 1 hari (bukan 30)
        self.key_history = []
        self.load_keys()
        self.start_auto_rotation()
    
    def start_auto_rotation(self):
        """Start background thread for auto-rotation"""
        def rotate_loop():
            while True:
                time.sleep(3600)  # Cek setiap 1 jam
                self.check_and_rotate()
        
        thread = threading.Thread(target=rotate_loop, daemon=True)
        thread.start()
        logger.info("✅ Auto-rotation started (check every 1 hour)")
    
    def generate_key(self, length: int = 32) -> str:
        return secrets.token_urlsafe(length)
    
    def create_key(self, key_id: str, rotated_by: str = "system") -> KeyEntry:
        key_value = self.generate_key()
        now = time.time()
        key = KeyEntry(
            key_id=key_id,
            key_value=key_value,
            created_at=now,
            expires_at=now + (self.rotation_interval * 86400),
            rotated_by=rotated_by
        )
        self.keys[key_id] = key
        self.current_key_id = key_id
        self.key_history.append({
            "key_id": key_id,
            "action": "CREATED",
            "timestamp": now,
            "rotated_by": rotated_by
        })
        self.save_keys()
        return key
    
    def rotate_key(self, key_id: str, rotated_by: str = "system") -> Optional[KeyEntry]:
        if key_id in self.keys:
            self.keys[key_id].is_active = False
        new_key_id = f"{key_id}_{int(time.time())}"
        return self.create_key(new_key_id, rotated_by)
    
    def check_and_rotate(self) -> Optional[KeyEntry]:
        if not self.current_key_id or self.current_key_id not in self.keys:
            return None
        key = self.keys[self.current_key_id]
        if time.time() > key.expires_at:
            logger.info(f"🔄 Key {self.current_key_id} expired, rotating...")
            return self.rotate_key(self.current_key_id, "auto_rotation")
        return None
    
    def get_current_key(self) -> Optional[KeyEntry]:
        if self.current_key_id and self.current_key_id in self.keys:
            return self.keys[self.current_key_id]
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_keys": len(self.keys),
            "active_keys": sum(1 for k in self.keys.values() if k.is_active),
            "current_key_id": self.current_key_id,
            "rotation_interval_days": self.rotation_interval,
            "history_count": len(self.key_history)
        }
    
    def save_keys(self):
        os.makedirs("private/keys", exist_ok=True)
        data = {
            "keys": {
                k: {
                    "key_id": v.key_id,
                    "key_value": v.key_value,
                    "created_at": v.created_at,
                    "expires_at": v.expires_at,
                    "is_active": v.is_active,
                    "rotated_by": v.rotated_by
                }
                for k, v in self.keys.items()
            },
            "current_key_id": self.current_key_id,
            "history": self.key_history
        }
        with open("private/keys/keys.json", "w") as f:
            json.dump(data, f, indent=2)
    
    def load_keys(self):
        try:
            with open("private/keys/keys.json", "r") as f:
                data = json.load(f)
                for key_id, key_data in data.get("keys", {}).items():
                    self.keys[key_id] = KeyEntry(
                        key_id=key_data["key_id"],
                        key_value=key_data["key_value"],
                        created_at=key_data["created_at"],
                        expires_at=key_data["expires_at"],
                        is_active=key_data["is_active"],
                        rotated_by=key_data["rotated_by"]
                    )
                self.current_key_id = data.get("current_key_id")
                self.key_history = data.get("history", [])
        except:
            pass

def get_key_rotation() -> KeyRotation:
    return KeyRotation()
