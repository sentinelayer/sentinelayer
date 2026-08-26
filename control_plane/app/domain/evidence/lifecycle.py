from datetime import datetime, timedelta
from typing import Dict

class EvidenceLifecycle:
    def __init__(self):
        self.evidence = {}
        self.retention_days = 7 * 365

    def create(self, evidence_id: str, data: dict) -> Dict:
        self.evidence[evidence_id] = {
            "data": data,
            "status": "CREATED",
            "created_at": datetime.utcnow().isoformat()
        }
        return self.evidence[evidence_id]

    def verify(self, evidence_id: str) -> Dict:
        if evidence_id not in self.evidence:
            return {"error": "Evidence not found"}
        self.evidence[evidence_id]["status"] = "VERIFIED"
        self.evidence[evidence_id]["verified_at"] = datetime.utcnow().isoformat()
        return self.evidence[evidence_id]

    def validate(self, evidence_id: str) -> Dict:
        if evidence_id not in self.evidence:
            return {"error": "Evidence not found"}
        self.evidence[evidence_id]["status"] = "VALID"
        self.evidence[evidence_id]["valid_at"] = datetime.utcnow().isoformat()
        return self.evidence[evidence_id]

    def expire(self, evidence_id: str) -> Dict:
        if evidence_id not in self.evidence:
            return {"error": "Evidence not found"}
        self.evidence[evidence_id]["status"] = "EXPIRED"
        self.evidence[evidence_id]["expired_at"] = datetime.utcnow().isoformat()
        return self.evidence[evidence_id]

    def revoke(self, evidence_id: str) -> Dict:
        if evidence_id not in self.evidence:
            return {"error": "Evidence not found"}
        self.evidence[evidence_id]["status"] = "REVOKED"
        self.evidence[evidence_id]["revoked_at"] = datetime.utcnow().isoformat()
        return self.evidence[evidence_id]

    def get_status(self, evidence_id: str) -> Dict:
        if evidence_id not in self.evidence:
            return {"status": "NOT_FOUND"}
        return {"status": self.evidence[evidence_id]["status"]}

    def is_valid(self, evidence_id: str) -> bool:
        if evidence_id not in self.evidence:
            return False
        return self.evidence[evidence_id]["status"] in ["VERIFIED", "VALID"]

    def auto_expire_old(self):
        cutoff = datetime.utcnow() - timedelta(days=self.retention_days)
        for eid, data in self.evidence.items():
            created = datetime.fromisoformat(data["created_at"])
            if created < cutoff:
                self.expire(eid)
