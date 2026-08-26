from datetime import datetime

class EvidenceLifecycle:
    def __init__(self):
        self.evidence = {}

    def create(self, evidence_id: str, data: dict):
        self.evidence[evidence_id] = {
            "data": data,
            "status": "CREATED",
            "created_at": datetime.utcnow().isoformat()
        }
        return self.evidence[evidence_id]

    def verify(self, evidence_id: str):
        if evidence_id in self.evidence:
            self.evidence[evidence_id]["status"] = "VERIFIED"
            return self.evidence[evidence_id]
        return {"error": "Evidence not found"}

    def expire(self, evidence_id: str):
        if evidence_id in self.evidence:
            self.evidence[evidence_id]["status"] = "EXPIRED"
            return self.evidence[evidence_id]
        return {"error": "Evidence not found"}
