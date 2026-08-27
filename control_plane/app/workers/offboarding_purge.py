from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime

from control_plane.app.infrastructure.db.models import Application, AuditEvent, LegalHoldRecord, OffboardingRequest, Policy, PolicyVersion
from control_plane.app.infrastructure.db.session import SessionLocal


def _audit(db, request: OffboardingRequest, detail: dict) -> None:
    previous = db.query(AuditEvent).filter(AuditEvent.tenant_id == request.tenant_id).order_by(
        AuditEvent.created_at.desc(), AuditEvent.id.desc()).first()
    now = datetime.now(UTC)
    event_id = str(uuid.uuid4())
    detail_json = json.dumps(detail, sort_keys=True, separators=(",", ":"))
    previous_hash = previous.event_hash if previous else None
    event_hash = hashlib.sha256("|".join([
        previous_hash or "", request.tenant_id, "maintenance-worker", "offboarding.purged",
        "offboarding_request", request.id, detail_json, now.isoformat(), event_id,
    ]).encode()).hexdigest()
    db.add(AuditEvent(
        id=event_id, tenant_id=request.tenant_id, actor_id="maintenance-worker",
        action="offboarding.purged", resource_type="offboarding_request", resource_id=request.id,
        detail=detail_json, previous_hash=previous_hash, event_hash=event_hash, created_at=now,
    ))


def purge_offboarded() -> dict[str, int]:
    """Purge scheduled resources after their retention boundary; preserve lifecycle evidence."""
    db = SessionLocal()
    try:
        now = datetime.now(UTC)
        records = db.query(OffboardingRequest).filter(
            OffboardingRequest.status.in_(["SCHEDULED", "COMPLETED"]),
            OffboardingRequest.hard_delete_at.is_not(None),
        ).all()
        purged = 0
        for request in records:
            boundary = request.hard_delete_at
            if boundary.tzinfo is None:
                boundary = boundary.replace(tzinfo=UTC)
            if boundary > now:
                continue
            active_hold = db.query(LegalHoldRecord).filter(
                LegalHoldRecord.tenant_id == request.tenant_id, LegalHoldRecord.status == "active"
            ).first()
            if active_hold:
                continue
            apps = db.query(Application).filter(Application.tenant_id == request.tenant_id).all()
            policies = db.query(Policy).filter(Policy.tenant_id == request.tenant_id).all()
            policy_ids = [policy.id for policy in policies]
            if policy_ids:
                db.query(PolicyVersion).filter(PolicyVersion.policy_id.in_(policy_ids)).delete(synchronize_session=False)
            for policy in policies:
                db.delete(policy)
            for app in apps:
                db.delete(app)
            request.status = "PURGED"
            request.completed_at = now
            _audit(db, request, {"applications": len(apps), "policies": len(policies)})
            purged += 1
        db.commit()
        return {"purged": purged}
    finally:
        db.close()
