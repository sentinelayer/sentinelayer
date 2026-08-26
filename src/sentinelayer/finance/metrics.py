from datetime import datetime, timedelta
from typing import Dict
from src.sentinelayer.database import SessionLocal
from src.sentinelayer.database.models import Subscription, Customer, Invoice

class FinanceMetrics:
    def __init__(self):
        self.db = SessionLocal()

    def calculate_mrr(self) -> float:
        subs = self.db.query(Subscription).filter_by(status="ACTIVE").all()
        return sum(s.price for s in subs)

    def calculate_arr(self) -> float:
        return self.calculate_mrr() * 12

    def calculate_cac(self, period_days: int = 90) -> float:
        customers = self.db.query(Customer).filter(Customer.created_at > (datetime.utcnow() - timedelta(days=period_days)).isoformat()).all()
        new = len([c for c in customers if c.status == "ACTIVE"])
        if new == 0:
            return 0.0
        return 8000 / new

    def calculate_ltv(self) -> float:
        avg_mrr = self.calculate_mrr() / max(1, self.db.query(Customer).filter_by(status="ACTIVE").count())
        return avg_mrr * 18

    def calculate_churn(self, period_days: int = 30) -> Dict:
        cutoff = (datetime.utcnow() - timedelta(days=period_days)).isoformat()
        start = self.db.query(Customer).filter(Customer.created_at < cutoff).count()
        end = self.db.query(Customer).filter_by(status="ACTIVE").count()
        if start == 0:
            return {"churn_rate": 0, "churned_customers": 0, "period_days": period_days}
        churned = start - end
        return {"churn_rate": (churned / start) * 100, "churned_customers": churned, "period_days": period_days}

    def get_financial_report(self) -> Dict:
        return {
            "mrr": self.calculate_mrr(),
            "arr": self.calculate_arr(),
            "cac": self.calculate_cac(),
            "ltv": self.calculate_ltv(),
            "ltv_cac_ratio": self.calculate_ltv() / max(1, self.calculate_cac()),
            "churn": self.calculate_churn(),
            "generated_at": datetime.utcnow().isoformat()
        }

finance = FinanceMetrics()
