import hashlib
from datetime import datetime

from control_plane.app.infrastructure.db.models import Evidence
from control_plane.app.infrastructure.db.session import SessionLocal


class EvidenceCollector:
    def collect(self, artifact: str, requirement_id: str, control_id: str) -> dict:
        db = SessionLocal()
        try:
            hash_value = hashlib.sha256(artifact.encode()).hexdigest()
            evidence = Evidence(
                artifact=artifact,
                requirement_id=requirement_id,
                control_id=control_id,
                status="CREATED",
                created_at=datetime.utcnow()
            )
            db.add(evidence)
            db.commit()
            db.refresh(evidence)
            return {
                "id": evidence.id,
                "artifact": artifact,
                "hash": hash_value,
                "status": evidence.status,
                "created_at": evidence.created_at.isoformat()
            }
        finally:
            db.close()
