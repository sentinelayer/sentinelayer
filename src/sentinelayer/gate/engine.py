import json
from datetime import datetime
from typing import Dict
from src.sentinelayer.database import SessionLocal
from src.sentinelayer.database.models import Requirement, GateResult

class AcceptanceGateEngine:
    def __init__(self):
        self.db = SessionLocal()
        self.rules = {
            "P0": {"required": True, "min_coverage": 95, "min_tests": 100},
            "P1": {"required": True, "min_coverage": 90, "min_tests": 90},
            "P2": {"required": False, "min_coverage": 80, "min_tests": 80},
            "P3": {"required": False, "min_coverage": 0, "min_tests": 0}
        }

    def evaluate(self, requirement_id: str) -> Dict:
        req = self.db.query(Requirement).filter_by(id=requirement_id).first()
        if not req:
            return {"status": "REJECTED", "reason": "Requirement not found"}
        checks = []
        results = []
        if req.implementation_status == "IMPLEMENTED":
            checks.append({"name": "Implementation", "status": "PASS"})
            results.append(True)
        else:
            checks.append({"name": "Implementation", "status": "FAIL", "reason": "Not implemented"})
            results.append(False)
        if req.test_count >= self.rules.get(req.criticality, {}).get("min_tests", 0):
            checks.append({"name": "Tests", "status": "PASS"})
            results.append(True)
        else:
            checks.append({"name": "Tests", "status": "FAIL", "reason": "Need more tests"})
            results.append(False)
        if req.coverage >= self.rules.get(req.criticality, {}).get("min_coverage", 0):
            checks.append({"name": "Coverage", "status": "PASS"})
            results.append(True)
        else:
            checks.append({"name": "Coverage", "status": "FAIL", "reason": "Need more coverage"})
            results.append(False)
        if req.evidence_valid:
            checks.append({"name": "Evidence", "status": "PASS"})
            results.append(True)
        else:
            checks.append({"name": "Evidence", "status": "FAIL", "reason": "Invalid evidence"})
            results.append(False)
        if req.reviewer_approved:
            checks.append({"name": "Reviewer", "status": "PASS"})
            results.append(True)
        else:
            checks.append({"name": "Reviewer", "status": "FAIL", "reason": "Not approved"})
            results.append(False)
        if not req.config_drift:
            checks.append({"name": "Drift", "status": "PASS"})
            results.append(True)
        else:
            checks.append({"name": "Drift", "status": "FAIL", "reason": "Configuration drift detected"})
            results.append(False)
        all_pass = all(results)
        status = "ACCEPTED" if all_pass else "REJECTED"
        gate_result = GateResult(
            requirement_id=requirement_id,
            status=status,
            checks=json.dumps(checks),
            evaluated_at=datetime.utcnow().isoformat()
        )
        self.db.add(gate_result)
        self.db.commit()
        return {
            "requirement_id": requirement_id,
            "status": status,
            "checks": checks,
            "all_pass": all_pass
        }

    def get_status(self, requirement_id: str) -> Dict:
        result = self.db.query(GateResult).filter_by(requirement_id=requirement_id).order_by(GateResult.evaluated_at.desc()).first()
        if result:
            return {"status": result.status, "checks": json.loads(result.checks), "evaluated_at": result.evaluated_at}
        return {"status": "NOT_EVALUATED"}

gate_engine = AcceptanceGateEngine()
