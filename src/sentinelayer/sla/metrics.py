from datetime import datetime, timedelta
from typing import Dict, List
from src.sentinelayer.database import SessionLocal
from src.sentinelayer.database.models import SLAMetric

class SLAManager:
    def __init__(self):
        self.db = SessionLocal()
        self.targets = {
            "availability": {"min": 99.9},
            "detection_rate": {"min": 95},
            "false_positive_rate": {"max": 5},
            "latency_p95": {"max": 20},
            "latency_p99": {"max": 50},
            "mttr": {"max": 60},
            "mttd": {"max": 15}
        }

    def record_metric(self, name: str, value: float) -> Dict:
        metric = SLAMetric(
            name=name,
            value=value,
            target=self.targets.get(name, {}),
            recorded_at=datetime.utcnow().isoformat()
        )
        target = self.targets.get(name, {})
        if "min" in target:
            metric.status = "PASS" if value >= target["min"] else "FAIL"
        elif "max" in target:
            metric.status = "PASS" if value <= target["max"] else "FAIL"
        else:
            metric.status = "UNKNOWN"
        self.db.add(metric)
        self.db.commit()
        return {"name": name, "value": value, "target": target, "status": metric.status}

    def get_metrics(self, hours: int = 24) -> List[Dict]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        metrics = self.db.query(SLAMetric).filter(SLAMetric.recorded_at > cutoff.isoformat()).all()
        return [{"name": m.name, "value": m.value, "target": m.target, "status": m.status, "recorded_at": m.recorded_at} for m in metrics]

    def get_sla_report(self, hours: int = 24) -> Dict:
        metrics = self.get_metrics(hours)
        total = len(metrics)
        if total == 0:
            return {"status": "NO_DATA", "total": 0}
        pass_count = sum(1 for m in metrics if m["status"] == "PASS")
        return {
            "total_metrics": total,
            "pass_count": pass_count,
            "fail_count": total - pass_count,
            "compliance_rate": (pass_count / total) * 100,
            "period_hours": hours
        }

sla_manager = SLAManager()
