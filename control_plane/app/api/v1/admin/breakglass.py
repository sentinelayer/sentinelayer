import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from control_plane.app.api.deps import db_with_tenant
from control_plane.app.infrastructure.db.models import AuditEvent, BreakGlassSession, User

router = APIRouter(prefix="/admin/breakglass", tags=["admin"])


class BreakGlassCreate(BaseModel):
    user_id: str
    reason: str = Field(min_length=1, max_length=2000)


class BreakGlassDecision(BaseModel):
    reason: str | None = Field(default=None, max_length=2000)


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
        previous_hash or "", tenant, actor, action, "breakglass_session", resource_id,
        detail_json, now.isoformat(), event_id,
    ]).encode()).hexdigest()
    db.add(AuditEvent(
        id=event_id, tenant_id=tenant, actor_id=actor, action=action,
        resource_type="breakglass_session", resource_id=resource_id, detail=detail_json,
        previous_hash=previous_hash, event_hash=digest, created_at=now,
    ))


def _expire_if_needed(session: BreakGlassSession, now: datetime) -> bool:
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if session.status in {"PENDING", "APPROVED"} and expires_at <= now:
        session.status = "EXPIRED"
        return True
    return False


def _serialize(session: BreakGlassSession) -> dict[str, Any]:
    return {
        "id": session.id,
        "tenant_id": session.tenant_id,
        "user_id": session.user_id,
        "requested_by": session.requested_by,
        "reason": session.reason,
        "status": session.status,
        "created_at": session.created_at.isoformat(),
        "expires_at": session.expires_at.isoformat(),
        "approved_by": session.approved_by,
        "approved_at": session.approved_at.isoformat() if session.approved_at else None,
        "revoked_at": session.revoked_at.isoformat() if session.revoked_at else None,
    }


@router.post("/")
@router.post("")
async def create_breakglass(
    data: BreakGlassCreate,
    request: Request,
    db: Session = Depends(db_with_tenant),
):
    actor, tenant = _require_admin(request)
    target = db.query(User).filter(User.id == data.user_id, User.tenant_id == tenant, User.is_active.is_(True)).first()
    if not target:
        raise HTTPException(status_code=404, detail="Active user not found for tenant")
    now = datetime.now(UTC)
    session = BreakGlassSession(
        id=str(uuid.uuid4()), tenant_id=tenant, user_id=target.id, requested_by=actor,
        reason=data.reason, status="PENDING", created_at=now, expires_at=now + timedelta(hours=1),
    )
    db.add(session)
    db.flush()
    _audit(db, tenant, actor, "breakglass.requested", session.id, {"user_id": target.id})
    db.commit()
    db.refresh(session)
    return _serialize(session)


@router.get("/")
@router.get("")
async def list_breakglass(request: Request, db: Session = Depends(db_with_tenant)):
    _, tenant = _require_admin(request)
    sessions = db.query(BreakGlassSession).filter(
        BreakGlassSession.tenant_id == tenant
    ).order_by(BreakGlassSession.created_at.desc()).all()
    changed = any(_expire_if_needed(session, datetime.now(UTC)) for session in sessions)
    if changed:
        db.commit()
    return [_serialize(session) for session in sessions]


@router.post("/{session_id}/approve")
async def approve_breakglass(
    session_id: str,
    request: Request,
    body: BreakGlassDecision | None = None,
    db: Session = Depends(db_with_tenant),
):
    actor, tenant = _require_admin(request)
    session = db.query(BreakGlassSession).filter(
        BreakGlassSession.id == session_id, BreakGlassSession.tenant_id == tenant
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Break-glass session not found")
    if _expire_if_needed(session, datetime.now(UTC)):
        db.commit()
    if session.status != "PENDING":
        raise HTTPException(status_code=409, detail=f"Session is {session.status.lower()}")
    if session.requested_by == actor:
        raise HTTPException(status_code=403, detail="Requester cannot approve their own break-glass session")
    session.status = "APPROVED"
    session.approved_by = actor
    session.approved_at = datetime.now(UTC)
    if body and body.reason:
        session.reason = f"{session.reason} | approval: {body.reason}"
    _audit(db, tenant, actor, "breakglass.approved", session.id, {"user_id": session.user_id})
    db.commit()
    db.refresh(session)
    return _serialize(session)


@router.post("/{session_id}/revoke")
async def revoke_breakglass(
    session_id: str,
    request: Request,
    body: BreakGlassDecision | None = None,
    db: Session = Depends(db_with_tenant),
):
    actor, tenant = _require_admin(request)
    session = db.query(BreakGlassSession).filter(
        BreakGlassSession.id == session_id, BreakGlassSession.tenant_id == tenant
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Break-glass session not found")
    if session.status not in {"PENDING", "APPROVED"}:
        raise HTTPException(status_code=409, detail=f"Session is {session.status.lower()}")
    session.status = "REVOKED"
    session.revoked_at = datetime.now(UTC)
    _audit(db, tenant, actor, "breakglass.revoked", session.id, {"reason": body.reason if body else None})
    db.commit()
    db.refresh(session)
    return _serialize(session)
