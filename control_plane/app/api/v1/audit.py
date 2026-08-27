from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from control_plane.app.api.deps import db_with_tenant, tenant_id
from control_plane.app.infrastructure.db.models import AuditEvent

router = APIRouter(prefix="/audit", tags=["audit"])


class AuditLogCreate(BaseModel):
    action: str = Field(min_length=1, max_length=128)
    resource: str = Field(min_length=1, max_length=64)
    resource_id: str | None = Field(default=None, max_length=128)
    data: dict[str, Any] = Field(default_factory=dict)


def _write_event(db: Session, tenant: str, actor: str | None, action: str,
                 resource: str, resource_id: str | None, detail: dict[str, Any]) -> AuditEvent:
    previous = db.query(AuditEvent).filter(AuditEvent.tenant_id == tenant).order_by(
        AuditEvent.created_at.desc(), AuditEvent.id.desc()).first()
    now = datetime.now(UTC)
    event_id = str(uuid.uuid4())
    detail_json = json.dumps(detail, sort_keys=True, separators=(",", ":"))
    previous_hash = previous.event_hash if previous else None
    event_hash = hashlib.sha256("|".join([
        previous_hash or "", tenant, actor or "", action, resource, resource_id or "",
        detail_json, now.isoformat(), event_id,
    ]).encode()).hexdigest()
    event = AuditEvent(
        id=event_id, tenant_id=tenant, actor_id=actor, action=action,
        resource_type=resource, resource_id=resource_id, detail=detail_json,
        previous_hash=previous_hash, event_hash=event_hash, created_at=now,
    )
    db.add(event)
    db.flush()
    return event


def _serialize(event: AuditEvent) -> dict[str, Any]:
    try:
        detail = json.loads(event.detail or "{}")
    except json.JSONDecodeError:
        detail = {"raw": event.detail}
    return {
        "id": event.id,
        "action": event.action,
        "resource": event.resource_type,
        "resource_id": event.resource_id,
        "data": detail.get("data", detail),
        "user_id": event.actor_id or "system",
        "tenant_id": event.tenant_id,
        "ip": detail.get("ip", "unknown"),
        "timestamp": event.created_at.isoformat(),
        "previous_hash": event.previous_hash,
        "event_hash": event.event_hash,
    }


@router.post("/log")
async def create_audit_log(data: AuditLogCreate, request: Request, db: Session = Depends(db_with_tenant)):
    tid = tenant_id(request)
    event = _write_event(
        db, tid, getattr(request.state, "user_id", None), data.action,
        data.resource, data.resource_id,
        {"data": data.data, "ip": request.client.host if request.client else "unknown"},
    )
    db.commit()
    db.refresh(event)
    return _serialize(event)


@router.get("/")
@router.get("")
async def get_audit_logs(
    request: Request,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(db_with_tenant),
):
    tid = tenant_id(request)
    events = db.query(AuditEvent).filter(AuditEvent.tenant_id == tid).order_by(
        AuditEvent.created_at.desc(), AuditEvent.id.desc()).limit(limit).all()
    return [_serialize(event) for event in events]


@router.get("/{resource}/{resource_id}")
async def get_audit_logs_by_resource(
    resource: str,
    resource_id: str,
    request: Request,
    db: Session = Depends(db_with_tenant),
):
    tid = tenant_id(request)
    events = db.query(AuditEvent).filter(
        AuditEvent.tenant_id == tid,
        AuditEvent.resource_type == resource,
        AuditEvent.resource_id == resource_id,
    ).order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc()).all()
    return [_serialize(event) for event in events]
