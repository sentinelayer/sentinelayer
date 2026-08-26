import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Optional
from cryptography.fernet import Fernet

class KeyRotation:
    def __init__(self):
        self.key_file = "private/keys.json"
        self.rotation_interval_hours = 24
        self.overlap_hours = 1
        self._load_keys()

    def _load_keys(self):
        if os.path.exists(self.key_file):
            with open(self.key_file, "r") as f:
                self.keys = json.load(f)
        else:
            self.keys = {"current": None, "previous": None, "last_rotation": None}

    def _save_keys(self):
        os.makedirs("private", exist_ok=True)
        with open(self.key_file, "w") as f:
            json.dump(self.keys, f, indent=2)

    def get_current_key(self) -> Optional[str]:
        return self.keys.get("current")

    def rotate(self) -> Dict:
        new_key = Fernet.generate_key().decode()
        old_key = self.keys.get("current")
        
        self.keys["previous"] = old_key
        self.keys["current"] = new_key
        self.keys["last_rotation"] = datetime.utcnow().isoformat()
        self._save_keys()
        
        return {
            "rotated_at": self.keys["last_rotation"],
            "new_key": new_key,
            "old_key": old_key
        }

    def check_rotation(self) -> Dict:
        if not self.keys.get("last_rotation"):
            return {"needs_rotation": True, "reason": "No previous rotation"}
        
        last = datetime.fromisoformat(self.keys["last_rotation"])
        if datetime.utcnow() - last > timedelta(hours=self.rotation_interval_hours):
            return {"needs_rotation": True, "reason": "Rotation interval exceeded"}
        
        return {"needs_rotation": False, "next_rotation": (last + timedelta(hours=self.rotation_interval_hours)).isoformat()}

key_rotation = KeyRotation()
