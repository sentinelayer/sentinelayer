import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List
from src.sentinelayer.database import SessionLocal
from src.sentinelayer.database.models import DriftEntry

class DriftDetector:
    def __init__(self):
        self.db = SessionLocal()
        self.iac_path = "infra/"

    def detect_drift(self, resource_type: str, actual: Dict) -> Dict:
        expected = self._get_expected(resource_type)
        if not expected:
            return {"drift": False, "reason": "No expected configuration found"}
        actual_hash = hashlib.sha256(json.dumps(actual, sort_keys=True).encode()).hexdigest()
        expected_hash = hashlib.sha256(json.dumps(expected, sort_keys=True).encode()).hexdigest()
        if actual_hash != expected_hash:
            drift = DriftEntry(resource_type=resource_type, expected=json.dumps(expected), actual=json.dumps(actual), detected_at=datetime.utcnow().isoformat(), status="DETECTED")
            self.db.add(drift)
            self.db.commit()
            return {"drift": True, "resource_type": resource_type, "expected": expected, "actual": actual}
        return {"drift": False, "reason": "Configuration matches expected"}

    def _get_expected(self, resource_type: str) -> Dict:
        path = os.path.join(self.iac_path, f"{resource_type}.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return {}

    def get_drifts(self) -> List[Dict]:
        drifts = self.db.query(DriftEntry).filter_by(status="DETECTED").all()
        return [{"resource_type": d.resource_type, "expected": json.loads(d.expected), "actual": json.loads(d.actual), "detected_at": d.detected_at} for d in drifts]

drift_detector = DriftDetector()
