from datetime import datetime
import json

class GateEngine:
    def __init__(self):
        self.requirements = {}

    def add_requirement(self, req_id: str, data: dict):
        self.requirements[req_id] = {
            **data,
            "status": "PENDING",
            "created_at": datetime.utcnow().isoformat()
        }
        return self.requirements[req_id]

    def evaluate(self, req_id: str) -> dict:
        req = self.requirements.get(req_id)
        if not req:
            return {"status": "REJECTED", "reason": "Requirement not found"}

        checks = []
        results = []

        checks.append({"name": "Implementation", "status": "PASS" if req.get("implemented", False) else "FAIL"})
        results.append(req.get("implemented", False))

        checks.append({"name": "Tests", "status": "PASS" if req.get("tested", False) else "FAIL"})
        results.append(req.get("tested", False))

        checks.append({"name": "Evidence", "status": "PASS" if req.get("has_evidence", False) else "FAIL"})
        results.append(req.get("has_evidence", False))

        checks.append({"name": "Reviewer", "status": "PASS" if req.get("reviewed", False) else "FAIL"})
        results.append(req.get("reviewed", False))

        checks.append({"name": "Residual Risk", "status": "PASS" if req.get("risk_accepted", False) else "FAIL"})
        results.append(req.get("risk_accepted", False))

        checks.append({"name": "Rollback Test", "status": "PASS" if req.get("rollback_tested", False) else "FAIL"})
        results.append(req.get("rollback_tested", False))

        all_pass = all(results)
        status = "ACCEPTED" if all_pass else "REJECTED"

        return {
            "requirement_id": req_id,
            "status": status,
            "checks": checks,
            "all_pass": all_pass,
            "evaluated_at": datetime.utcnow().isoformat()
        }

    def get_status(self, req_id: str) -> dict:
        req = self.requirements.get(req_id)
        if not req:
            return {"status": "NOT_FOUND"}
        return {"status": req.get("status", "PENDING")}
