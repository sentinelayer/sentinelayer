from datetime import datetime, timedelta

class EmergencyBypass:
    def __init__(self):
        self.bypasses = {}

    def activate(self, bypass_id: str, reason: str, duration_minutes: int = 60) -> dict:
        self.bypasses[bypass_id] = {
            "reason": reason,
            "duration_minutes": duration_minutes,
            "active": True,
            "activated_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(minutes=duration_minutes)).isoformat()
        }
        return {
            "bypass_id": bypass_id,
            "status": "activated",
            "expires_at": self.bypasses[bypass_id]["expires_at"]
        }

    def deactivate(self, bypass_id: str) -> dict:
        if bypass_id in self.bypasses:
            self.bypasses[bypass_id]["active"] = False
            return {"bypass_id": bypass_id, "status": "deactivated"}
        return {"error": "Bypass not found"}

    def is_active(self, bypass_id: str) -> bool:
        return self.bypasses.get(bypass_id, {}).get("active", False)

    def get_active_bypasses(self) -> list:
        return [{"id": k, **v} for k, v in self.bypasses.items() if v["active"]]

    def emergency_action_log(self, action: str, reason: str) -> dict:
        return {
            "action": action,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
            "requires_review": True,
            "review_deadline": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
