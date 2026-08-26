from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from control_plane.app.infrastructure.db.session import SessionLocal
from control_plane.app.domain.offboarding.entity import OffboardingRequest

def purge_offboarded():
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=7)
        old_requests = db.query(OffboardingRequest).filter(OffboardingRequest.hard_delete_at < cutoff).all()
        for req in old_requests:
            db.delete(req)
        db.commit()
        return {"purged": len(old_requests)}
    finally:
        db.close()
