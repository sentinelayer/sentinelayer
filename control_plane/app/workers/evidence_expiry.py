from datetime import datetime, timedelta

from control_plane.app.infrastructure.db.models import Evidence
from control_plane.app.infrastructure.db.session import SessionLocal


def expire_old_evidence():
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=30)
        old_evidence = db.query(Evidence).filter(Evidence.created_at < cutoff).all()
        expired_count = 0
        for ev in old_evidence:
            if ev.status != "EXPIRED":
                ev.status = "EXPIRED"
                expired_count += 1
        db.commit()
        return {"expired": expired_count}
    finally:
        db.close()
