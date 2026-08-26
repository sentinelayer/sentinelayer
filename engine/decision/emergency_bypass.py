class EmergencyBypass:
    def __init__(self):
        self.active_bypasses = {}

    def activate(self, bypass_id: str, reason: str, duration_minutes: int = 60):
        self.active_bypasses[bypass_id] = {
            "reason": reason,
            "duration_minutes": duration_minutes,
            "active": True
        }
        return {"bypass_id": bypass_id, "status": "activated"}

    def deactivate(self, bypass_id: str):
        if bypass_id in self.active_bypasses:
            self.active_bypasses[bypass_id]["active"] = False
            return {"bypass_id": bypass_id, "status": "deactivated"}
        return {"error": "Bypass not found"}

    def is_active(self, bypass_id: str) -> bool:
        return self.active_bypasses.get(bypass_id, {}).get("active", False)
