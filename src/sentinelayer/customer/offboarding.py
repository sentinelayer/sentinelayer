from datetime import datetime, timedelta
import uuid
from typing import Dict
from src.sentinelayer.database import SessionLocal
from src.sentinelayer.database.models import Customer, OffboardingRequest

class OffboardingManager:
    def __init__(self):
        self.db = SessionLocal()
        self.retention_days = 30
        self.delete_delay_days = 7

    def start_offboarding(self, customer_id: str, reason: str) -> Dict:
        customer = self.db.query(Customer).filter_by(id=customer_id).first()
        if not customer:
            return {"error": "Customer not found"}
        request = OffboardingRequest(
            id=str(uuid.uuid4()),
            customer_id=customer_id,
            reason=reason,
            status="ONBOARDING",
            started_at=datetime.utcnow().isoformat(),
            soft_delete_at=(datetime.utcnow() + timedelta(days=self.retention_days)).isoformat(),
            hard_delete_at=(datetime.utcnow() + timedelta(days=self.retention_days + self.delete_delay_days)).isoformat()
        )
        self.db.add(request)
        self.db.commit()
        return {"id": request.id, "status": request.status, "soft_delete_at": request.soft_delete_at, "hard_delete_at": request.hard_delete_at}

    def execute_soft_delete(self, customer_id: str) -> Dict:
        customer = self.db.query(Customer).filter_by(id=customer_id).first()
        if not customer:
            return {"error": "Customer not found"}
        customer.status = "SOFT_DELETED"
        self.db.commit()
        return {"customer_id": customer_id, "status": "SOFT_DELETED"}

    def execute_hard_delete(self, customer_id: str) -> Dict:
        customer = self.db.query(Customer).filter_by(id=customer_id).first()
        if not customer:
            return {"error": "Customer not found"}
        self.db.delete(customer)
        self.db.commit()
        return {"customer_id": customer_id, "status": "HARD_DELETED"}

    def restore_customer(self, customer_id: str) -> Dict:
        customer = self.db.query(Customer).filter_by(id=customer_id).first()
        if not customer:
            return {"error": "Customer not found"}
        customer.status = "ACTIVE"
        self.db.commit()
        return {"customer_id": customer_id, "status": "RESTORED"}

offboarding = OffboardingManager()
