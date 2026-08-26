import os
from typing import Dict, List
from src.sentinelayer.database import SessionLocal
from src.sentinelayer.database.models import DataResidencyRule

class ResidencyManager:
    def __init__(self):
        self.db = SessionLocal()
        self.default_region = os.getenv("DEFAULT_REGION", "id")
        self.allowed_regions = os.getenv("ALLOWED_REGIONS", "id,us,eu,sg").split(",")

    def enforce_residency(self, data_type: str, requested_region: str) -> Dict:
        rule = self.db.query(DataResidencyRule).filter_by(data_type=data_type).first()
        if not rule:
            return {"allowed": requested_region in self.allowed_regions, "region": self.default_region}
        if requested_region not in rule.allowed_regions:
            return {"allowed": False, "region": rule.primary_region, "reason": f"Data type {data_type} must be stored in {rule.primary_region}"}
        return {"allowed": True, "region": requested_region}

    def get_residency_rules(self) -> List[Dict]:
        rules = self.db.query(DataResidencyRule).all()
        return [{"data_type": r.data_type, "primary_region": r.primary_region, "backup_region": r.backup_region, "allowed_regions": r.allowed_regions} for r in rules]

    def validate_export(self, data_type: str, target_region: str) -> bool:
        result = self.enforce_residency(data_type, target_region)
        return result["allowed"]

residency = ResidencyManager()
