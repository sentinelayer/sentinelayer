from datetime import datetime, timedelta


class DeletionSemantics:
    def __init__(self):
        self.soft_delete_retention_days = 30
        self.hard_delete_delay_days = 7
        self.evidence_retention_years = 7

    def soft_delete(self, customer_id: str) -> dict:
        return {
            "customer_id": customer_id,
            "status": "SOFT_DELETED",
            "soft_delete_at": datetime.utcnow().isoformat(),
            "hard_delete_at": (datetime.utcnow() + timedelta(days=self.hard_delete_delay_days)).isoformat()
        }

    def hard_delete(self, customer_id: str) -> dict:
        return {
            "customer_id": customer_id,
            "status": "HARD_DELETED",
            "hard_delete_at": datetime.utcnow().isoformat(),
            "evidence_retention_until": (datetime.utcnow() + timedelta(days=self.evidence_retention_years * 365)).isoformat()
        }

    def purge_delete(self, customer_id: str) -> dict:
        return {
            "customer_id": customer_id,
            "status": "PURGED",
            "purged_at": datetime.utcnow().isoformat()
        }
