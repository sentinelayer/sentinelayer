from datetime import datetime
import hashlib
import os
from typing import Dict, List
from src.sentinelayer.database import SessionLocal
from src.sentinelayer.database.models import ControlEvidence

class ControlEvidenceMatrix:
    def __init__(self):
        self.db = SessionLocal()

    def add_evidence(self, requirement_id: str, control_id: str, artifact: str, status: str) -> Dict:
        evidence = ControlEvidence(
            requirement_id=requirement_id,
            control_id=control_id,
            artifact=artifact,
            status=status,
            recorded_at=datetime.utcnow().isoformat()
        )
        self.db.add(evidence)
        self.db.commit()
        return {
            "id": evidence.id,
            "requirement_id": requirement_id,
            "control_id": control_id,
            "status": status
        }

    def get_matrix(self, requirement_id: str = None) -> List[Dict]:
        query = self.db.query(ControlEvidence)
        if requirement_id:
            query = query.filter_by(requirement_id=requirement_id)
        results = query.all()
        return [{
            "requirement_id": r.requirement_id,
            "control_id": r.control_id,
            "artifact": r.artifact,
            "status": r.status,
            "recorded_at": r.recorded_at
        } for r in results]

    def verify_evidence(self, evidence_id: str) -> Dict:
        evidence = self.db.query(ControlEvidence).filter_by(id=evidence_id).first()
        if not evidence:
            return {"error": "Evidence not found"}
        if os.path.exists(evidence.artifact):
            with open(evidence.artifact, "rb") as f:
                hash_value = hashlib.sha256(f.read()).hexdigest()
            evidence.hash_value = hash_value
            evidence.verified_at = datetime.utcnow().isoformat()
            evidence.status = "VERIFIED"
            self.db.commit()
            return {"id": evidence.id, "status": "VERIFIED", "hash": hash_value}
        evidence.status = "MISSING"
        self.db.commit()
        return {"id": evidence.id, "status": "MISSING", "reason": "Artifact not found"}

    def get_compliance_summary(self) -> Dict:
        evidences = self.db.query(ControlEvidence).all()
        total = len(evidences)
        if total == 0:
            return {"total": 0, "verified": 0, "missing": 0, "compliance": 0}
        verified = len([e for e in evidences if e.status == "VERIFIED"])
        missing = len([e for e in evidences if e.status == "MISSING"])
        return {
            "total": total,
            "verified": verified,
            "missing": missing,
            "compliance": (verified / total) * 100
        }

evidence_matrix = ControlEvidenceMatrix()
