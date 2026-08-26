from datetime import datetime, timedelta


class OffboardingLifecycle:
    def __init__(self):
        self.retention_days = 30
        self.delete_delay_days = 7

    def start_offboarding(self, customer_id: str):
        return {
            "customer_id": customer_id,
            "status": "ONBOARDING",
            "soft_delete_at": (datetime.utcnow() + timedelta(days=self.retention_days)).isoformat(),
            "hard_delete_at": (datetime.utcnow() + timedelta(days=self.retention_days + self.delete_delay_days)).isoformat()
        }

    def complete_offboarding(self, customer_id: str):
        return {"customer_id": customer_id, "status": "OFFBOARDING_COMPLETED"}

    def get_status(self, customer_id: str):
        return {"customer_id": customer_id, "status": "ACTIVE"}
