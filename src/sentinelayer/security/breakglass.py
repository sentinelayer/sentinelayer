from datetime import datetime, timedelta
import uuid
import os
from typing import Dict
from src.sentinelayer.database import SessionLocal
from src.sentinelayer.database.models import BreakGlassAccess

class BreakGlassManager:
    def __init__(self):
        self.db = SessionLocal()
        self.default_duration_hours = int(os.getenv("BREAK_GLASS_DURATION_HOURS", "1"))

    def request_access(self, user_id: str, reason: str, duration_hours: int = None) -> Dict:
        duration = duration_hours or self.default_duration_hours
        access = BreakGlassAccess(
            id=str(uuid.uuid4()),
            user_id=user_id,
            reason=reason,
            status="PENDING",
            requested_at=datetime.utcnow().isoformat(),
            duration_hours=duration,
            expires_at=(datetime.utcnow() + timedelta(hours=duration)).isoformat()
        )
        self.db.add(access)
        self.db.commit()
        return {"id": access.id, "status": access.status, "expires_at": access.expires_at}

    def approve_access(self, access_id: str, approver_id: str) -> Dict:
        access = self.db.query(BreakGlassAccess).filter_by(id=access_id).first()
        if not access:
            return {"error": "Access request not found"}
        access.status = "APPROVED"
        access.approved_by = approver_id
        access.approved_at = datetime.utcnow().isoformat()
        self.db.commit()
        return {"id": access.id, "status": access.status, "expires_at": access.expires_at}

    def revoke_access(self, access_id: str) -> Dict:
        access = self.db.query(BreakGlassAccess).filter_by(id=access_id).first()
        if not access:
            return {"error": "Access not found"}
        access.status = "REVOKED"
        access.revoked_at = datetime.utcnow().isoformat()
        self.db.commit()
        return {"id": access.id, "status": access.status}

    def check_access(self, user_id: str) -> bool:
        access = self.db.query(BreakGlassAccess).filter_by(user_id=user_id, status="APPROVED").first()
        if not access:
            return False
        if datetime.utcnow() > datetime.fromisoformat(access.expires_at):
            access.status = "EXPIRED"
            self.db.commit()
            return False
        return True

    def get_active_break_glass(self) -> list:
        results = self.db.query(BreakGlassAccess).filter_by(status="APPROVED").all()
        return [{"id": r.id, "user_id": r.user_id, "reason": r.reason, "expires_at": r.expires_at} for r in results]

break_glass = BreakGlassManager()
