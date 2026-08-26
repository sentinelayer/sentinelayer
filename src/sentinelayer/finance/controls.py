from datetime import datetime
from typing import Dict
from src.sentinelayer.database import SessionLocal
from src.sentinelayer.database.models import CostEntry, Customer, Invoice

class FinancialControls:
    def __init__(self):
        self.db = SessionLocal()
        self.budget_limit = 10000

    def track_cost(self, category: str, amount: float, description: str) -> Dict:
        cost = CostEntry(
            category=category,
            amount=amount,
            description=description,
            timestamp=datetime.utcnow().isoformat()
        )
        self.db.add(cost)
        self.db.commit()
        return {"category": category, "amount": amount, "timestamp": cost.timestamp}

    def get_monthly_costs(self) -> Dict:
        month_start = datetime.utcnow().replace(day=1).isoformat()
        costs = self.db.query(CostEntry).filter(CostEntry.timestamp >= month_start).all()
        total = sum(c.amount for c in costs)
        by_category = {}
        for c in costs:
            by_category[c.category] = by_category.get(c.category, 0) + c.amount
        return {
            "total": total,
            "budget_limit": self.budget_limit,
            "remaining": self.budget_limit - total,
            "by_category": by_category,
            "over_budget": total > self.budget_limit
        }

    def get_cost_to_serve(self, customer_id: str) -> float:
        customer = self.db.query(Customer).filter_by(id=customer_id).first()
        if not customer:
            return 0.0
        costs = self.db.query(CostEntry).filter_by(customer_id=customer_id).all()
        return sum(c.amount for c in costs)

    def get_margin(self, customer_id: str) -> Dict:
        revenue = self.db.query(Invoice).filter_by(customer_id=customer_id).all()
        total_revenue = sum(r.amount for r in revenue)
        cost_to_serve = self.get_cost_to_serve(customer_id)
        if total_revenue == 0:
            return {"margin": 0, "revenue": 0, "cost": cost_to_serve}
        margin = ((total_revenue - cost_to_serve) / total_revenue) * 100
        return {"revenue": total_revenue, "cost": cost_to_serve, "margin": margin}

finance_controls = FinancialControls()
