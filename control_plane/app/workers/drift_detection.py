import json
import hashlib
import os
from datetime import datetime
from typing import Dict

class DriftDetection:
    def __init__(self):
        self.expected_config = {}

    def load_expected(self, path: str):
        if os.path.exists(path):
            with open(path, "r") as f:
                self.expected_config = json.load(f)

    def detect_drift(self, actual_config: Dict) -> Dict:
        expected_hash = hashlib.sha256(json.dumps(self.expected_config, sort_keys=True).encode()).hexdigest()
        actual_hash = hashlib.sha256(json.dumps(actual_config, sort_keys=True).encode()).hexdigest()
        
        if expected_hash != actual_hash:
            return {
                "drift_detected": True,
                "detected_at": datetime.utcnow().isoformat(),
                "expected_hash": expected_hash,
                "actual_hash": actual_hash
            }
        return {"drift_detected": False}
