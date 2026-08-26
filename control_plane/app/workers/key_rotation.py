import os
from datetime import datetime, timedelta

class KeyRotationWorker:
    def __init__(self):
        self.rotation_interval_hours = 24
        self.overlap_hours = 1
        self.keys = {
            "current": os.getenv("POLICY_SIGNING_SECRET"),
            "previous": None,
            "last_rotation": None
        }

    def rotate(self) -> Dict:
        import uuid
        self.keys["previous"] = self.keys["current"]
        self.keys["current"] = str(uuid.uuid4())
        self.keys["last_rotation"] = datetime.utcnow().isoformat()
        return {"rotated_at": self.keys["last_rotation"], "new_key": self.keys["current"]}

    def check_rotation(self) -> Dict:
        if not self.keys["last_rotation"]:
            return {"needs_rotation": True}
        last = datetime.fromisoformat(self.keys["last_rotation"])
        if datetime.utcnow() - last > timedelta(hours=self.rotation_interval_hours):
            return {"needs_rotation": True}
        return {"needs_rotation": False}
