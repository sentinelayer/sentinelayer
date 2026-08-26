from datetime import datetime
import json

class AuditTrail:
    def __init__(self):
        self.entries = []

    def log(self, action: str, data: dict) -> dict:
        entry = {
            "action": action,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.entries.append(entry)
        return entry

    def get_logs(self, limit: int = 100):
        return self.entries[-limit:]

    def search(self, action: str):
        return [e for e in self.entries if e["action"] == action]
