import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from control_plane.app.api.deps import db_with_tenant
from control_plane.app.infrastructure.db.models import AuditEvent, HighRiskActionRecord

router = APIRouter(prefix="/admin/high-risk-actions", tags=["admin"])


class HighRiskAction(BaseModel):
    action: str
    reason: str = Field(min_length=1, max_length=2000)


ALLOWED_ACTIONS = {"block_tenant", "revoke_all_tokens", "disable_waf", "force_rotation"}


def _require_admin(request: Request) -> tuple[str, str]:
    actor = getattr(request.state, "user_id", None)
    tenant = getattr(request.state, "tenant_id", None)
    if not actor or not tenant or not getattr(request.state, "is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return actor, tenant


def _audit(db: Session, tenant: str, actor: str, action: str, resource_id: str, detail: dict[str, Any]) -> None:
    previous = db.query(AuditEvent).filter(AuditEvent.tenant_id == tenant).order_by(
        AuditEvent.created_at.desc(), AuditEvent.id.desc()).first()
    now = datetime.now(UTC)
    event_id = str(uuid.uuid4())
    detail_json = json.dumps(detail, sort_keys=True, separators=(",", ":"))
    previous_hash = previous.event_hash if previous else None
    digest = hashlib.sha256("|".join([
        previous_hash or "", tenant, actor, action, "high_risk_action", resource_id,
        detail_json, now.isoformat(), event_id,
    ]).encode()).hexdigest()
    db.add(AuditEvent(
        id=event_id, tenant_id=tenant, actor_id=actor, action=action,
        resource_type="high_risk_action", resource_id=resource_id, detail=detail_json,
        previous_hash=previous_hash, event_hash=digest, created_at=now,
    ))


def _serialize(record: HighRiskActionRecord) -> dict[str, Any]:
    return {
        "id": record.id,
        "tenant_id": record.tenant_id,
        "action": record.action,
        "reason": record.reason,
        "requested_by": record.requested_by,
        "approved_by": record.approved_by,
        "rejected_by": record.rejected_by,
        "status": record.status,
        "requested_at": record.requested_at.isoformat(),
        "approved_at": record.approved_at.isoformat() if record.approved_at else None,
        "rejected_at": record.rejected_at.isoformat() if record.rejected_at else None,
        "requires_approval": True,
    }


@router.post("/")
@router.post("")
async def execute_high_risk_action(
    data: HighRiskAction,
    request: Request,
    db: Session = Depends(db_with_tenant),
):
    actor, tenant = _require_admin(request)
    if data.action not in ALLOWED_ACTIONS:
        raise HTTPException(status_code=400, detail="Invalid action")
    record = HighRiskActionRecord(
        id=str(uuid.uuid4()), tenant_id=tenant, action=data.action, reason=data.reason,
        requested_by=actor, status="PENDING_APPROVAL", requested_at=datetime.now(UTC),
    )
    db.add(record)
    db.flush()
    _audit(db, tenant, actor, "high_risk_action.requested", record.id, {"action": data.action})
    db.commit()
    db.refresh(record)
    return _serialize(record)


@router.get("/")
@router.get("")
async def list_high_risk_actions(request: Request, db: Session = Depends(db_with_tenant)):
    _, tenant = _require_admin(request)
    records = db.query(HighRiskActionRecord).filter(
        HighRiskActionRecord.tenant_id == tenant
    ).order_by(HighRiskActionRecord.requested_at.desc()).all()
    return [_serialize(record) for record in records]


@router.post("/{id}/approve")
async def approve_high_risk_action(id: str, request: Request, db: Session = Depends(db_with_tenant)):
    actor, tenant = _require_admin(request)
    record = db.query(HighRiskActionRecord).filter(
        HighRiskActionRecord.id == id, HighRiskActionRecord.tenant_id == tenant
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Action not found")
    if record.status != "PENDING_APPROVAL":
        raise HTTPException(status_code=409, detail="Action is not pending approval")
    if record.requested_by == actor:
        raise HTTPException(status_code=403, detail="Requester cannot approve their own action")
    record.status = "APPROVED"
    record.approved_by = actor
    record.approved_at = datetime.now(UTC)
    _audit(db, tenant, actor, "high_risk_action.approved", record.id, {"action": record.action})
    db.commit()
    db.refresh(record)
    return _serialize(record)


@router.post("/{id}/reject")
async def reject_high_risk_action(id: str, request: Request, db: Session = Depends(db_with_tenant)):
    actor, tenant = _require_admin(request)
    record = db.query(HighRiskActionRecord).filter(
        HighRiskActionRecord.id == id, HighRiskActionRecord.tenant_id == tenant
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Action not found")
    if record.status != "PENDING_APPROVAL":
        raise HTTPException(status_code=409, detail="Action is not pending approval")
    record.status = "REJECTED"
    record.rejected_by = actor
    record.rejected_at = datetime.now(UTC)
    _audit(db, tenant, actor, "high_risk_action.rejected", record.id, {"action": record.action})
    db.commit()
    db.refresh(record)
    return _serialize(record)
