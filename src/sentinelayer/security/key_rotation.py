import os
from datetime import datetime

class KeyRotation:
    def __init__(self):
        self.last_rotation = None
    
    def rotate(self):
        self.last_rotation = datetime.utcnow().isoformat()
        return {"rotated_at": self.last_rotation}
    
    def get_status(self):
        return {"last_rotation": self.last_rotation}

key_rotation = KeyRotation()
