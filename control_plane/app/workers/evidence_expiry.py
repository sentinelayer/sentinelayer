from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from control_plane.app.infrastructure.db.session import SessionLocal
from control_plane.app.domain.evidence.entity import Evidence

def expire_old_evidence():
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=30)
        old_evidence = db.query(Evidence).filter(Evidence.created_at < cutoff).all()
        for ev in old_evidence:
            if ev.status != "EXPIRED":
                ev.status = "EXPIRED"
        db.commit()
        return {"expired": len(old_evidence)}
    finally:
        db.close()
