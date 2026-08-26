from datetime import datetime, timedelta
import uuid
import os
from typing import Dict
from src.sentinelayer.database import SessionLocal
from src.sentinelayer.database.models import ReviewRequest, ReviewLog

class IndependentReviewer:
    def __init__(self):
        self.db = SessionLocal()
        self.external_email = os.getenv("EXTERNAL_REVIEWER_EMAIL", "reviewer@sentinelayer.com")
        self.approval_timeout_hours = {"emergency": 24, "high": 4, "medium": 24, "low": 72}

    def request_review(self, change_id: str, severity: str, description: str) -> Dict:
        request = ReviewRequest(
            id=str(uuid.uuid4()),
            change_id=change_id,
            severity=severity,
            description=description,
            status="PENDING",
            requested_at=datetime.utcnow().isoformat(),
            due_at=(datetime.utcnow() + timedelta(hours=self.approval_timeout_hours.get(severity, 24))).isoformat()
        )
        self.db.add(request)
        self.db.commit()
        return {"id": request.id, "status": request.status, "due_at": request.due_at}

    def approve_review(self, request_id: str, notes: str = "") -> Dict:
        request = self.db.query(ReviewRequest).filter_by(id=request_id).first()
        if not request:
            return {"error": "Review request not found"}
        request.status = "APPROVED"
        request.approved_at = datetime.utcnow().isoformat()
        request.notes = notes
        self.db.commit()
        return {"id": request.id, "status": request.status}

    def reject_review(self, request_id: str, reason: str) -> Dict:
        request = self.db.query(ReviewRequest).filter_by(id=request_id).first()
        if not request:
            return {"error": "Review request not found"}
        request.status = "REJECTED"
        request.rejected_at = datetime.utcnow().isoformat()
        request.rejection_reason = reason
        self.db.commit()
        return {"id": request.id, "status": request.status}

    def emergency_action_log(self, action: str, description: str) -> Dict:
        log = ReviewLog(
            id=str(uuid.uuid4()),
            action=action,
            description=description,
            severity="EMERGENCY",
            logged_at=datetime.utcnow().isoformat(),
            review_deadline=(datetime.utcnow() + timedelta(hours=24)).isoformat()
        )
        self.db.add(log)
        self.db.commit()
        return {"id": log.id, "action": log.action, "review_deadline": log.review_deadline}

reviewer = IndependentReviewer()
