import json
from datetime import datetime, timedelta
from typing import Dict, List
from src.sentinelayer.database import SessionLocal
from src.sentinelayer.database.models import Customer, CustomerActivity

class SuccessMetrics:
    def __init__(self):
        self.db = SessionLocal()

    def track_activity(self, customer_id: str, activity_type: str, data: Dict) -> Dict:
        activity = CustomerActivity(
            customer_id=customer_id,
            activity_type=activity_type,
            data=json.dumps(data),
            occurred_at=datetime.utcnow().isoformat()
        )
        self.db.add(activity)
        self.db.commit()
        return {"customer_id": customer_id, "activity_type": activity_type, "timestamp": activity.occurred_at}

    def get_time_to_value(self, customer_id: str) -> Dict:
        customer = self.db.query(Customer).filter_by(id=customer_id).first()
        if not customer:
            return {"error": "Customer not found"}
        first = self.db.query(CustomerActivity).filter_by(customer_id=customer_id).order_by(CustomerActivity.occurred_at).first()
        if not first:
            return {"time_to_value": None, "status": "NO_ACTIVITY"}
        activation = self.db.query(CustomerActivity).filter_by(customer_id=customer_id, activity_type="ACTIVATION").first()
        if not activation:
            return {"time_to_value": None, "status": "NOT_ACTIVATED"}
        ttv = (datetime.fromisoformat(activation.occurred_at) - datetime.fromisoformat(first.occurred_at)).days
        return {"customer_id": customer_id, "time_to_value_days": ttv, "status": "ACTIVATED"}

    def get_retention(self, customer_id: str) -> Dict:
        customer = self.db.query(Customer).filter_by(id=customer_id).first()
        if not customer:
            return {"error": "Customer not found"}
        activities = self.db.query(CustomerActivity).filter_by(customer_id=customer_id).all()
        if len(activities) < 2:
            return {"retention_days": 0, "status": "INSUFFICIENT_DATA"}
        first = datetime.fromisoformat(activities[0].occurred_at)
        last = datetime.fromisoformat(activities[-1].occurred_at)
        return {"customer_id": customer_id, "retention_days": (last - first).days, "status": "ACTIVE"}

    def get_usage(self, customer_id: str) -> Dict:
        activities = self.db.query(CustomerActivity).filter_by(customer_id=customer_id).all()
        usage_by_type = {}
        for a in activities:
            usage_by_type[a.activity_type] = usage_by_type.get(a.activity_type, 0) + 1
        return {"customer_id": customer_id, "total_activities": len(activities), "usage_by_type": usage_by_type}

success = SuccessMetrics()
