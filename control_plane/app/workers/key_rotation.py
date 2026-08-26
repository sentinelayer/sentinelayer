import os
from datetime import datetime, timedelta

class KeyRotation:
    def __init__(self):
        self.last_rotation = datetime.utcnow()
        self.interval_hours = 24

    def rotate(self):
        self.last_rotation = datetime.utcnow()
        return {"rotated_at": self.last_rotation.isoformat()}

    def check_rotation(self):
        if datetime.utcnow() - self.last_rotation > timedelta(hours=self.interval_hours):
            return {"needs_rotation": True}
        return {"needs_rotation": False}
