from datetime import datetime


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

    def get_logs(self, limit: int = 100) -> list:
        return self.entries[-limit:]

    def search(self, action: str) -> list:
        return [e for e in self.entries if e["action"] == action]

    def get_by_user(self, user_id: str) -> list:
        return [e for e in self.entries if e["data"].get("user_id") == user_id]
