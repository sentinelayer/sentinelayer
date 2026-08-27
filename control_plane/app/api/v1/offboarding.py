"""Customer offboarding lifecycle — Blueprint §9.19."""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from control_plane.app.api.deps import db_with_tenant, tenant_id
from control_plane.app.infrastructure.db.models import Application, AuditEvent, OffboardingRequest, Policy

router = APIRouter(prefix="/offboarding", tags=["offboarding"])


class OffboardRequest(BaseModel):
    confirm: bool = False
    mode: str = Field(default="soft", pattern="^(soft|hard)$")


def _audit(db: Session, tenant: str, actor: str | None, request_id: str, detail: dict[str, Any]) -> None:
    previous = db.query(AuditEvent).filter(AuditEvent.tenant_id == tenant).order_by(
        AuditEvent.created_at.desc(), AuditEvent.id.desc()).first()
    now = datetime.now(UTC)
    event_id = str(uuid.uuid4())
    detail_json = json.dumps(detail, sort_keys=True, separators=(",", ":"))
    previous_hash = previous.event_hash if previous else None
    event_hash = hashlib.sha256("|".join([
        previous_hash or "", tenant, actor or "", "offboarding.requested", "offboarding_request",
        request_id, detail_json, now.isoformat(), event_id,
    ]).encode()).hexdigest()
    db.add(AuditEvent(
        id=event_id, tenant_id=tenant, actor_id=actor, action="offboarding.requested",
        resource_type="offboarding_request", resource_id=request_id, detail=detail_json,
        previous_hash=previous_hash, event_hash=event_hash, created_at=now,
    ))


@router.post("/request")
async def request_offboard(data: OffboardRequest, request: Request, db: Session = Depends(db_with_tenant)):
    tid = tenant_id(request)
    if not data.confirm:
        raise HTTPException(status_code=400, detail="confirm=true required")
    existing = db.query(OffboardingRequest).filter(
        OffboardingRequest.tenant_id == tid,
        OffboardingRequest.status.in_(["REQUESTED", "SCHEDULED"]),
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="An offboarding request is already scheduled")

    apps = db.query(Application).filter(Application.tenant_id == tid).all()
    policies = db.query(Policy).filter(Policy.tenant_id == tid).all()
    before = {"apps": [a.id for a in apps], "policies": [p.id for p in policies]}
    before_hash = hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest()
    now = datetime.now(UTC)
    hard_delete_at = now + (timedelta(days=7) if data.mode == "hard" else timedelta(days=37))
    status = "SCHEDULED" if data.mode == "hard" else "COMPLETED"
    if data.mode == "soft":
        for app in apps:
            if not app.name.startswith("[OFFBOARD]"):
                app.name = f"[OFFBOARD] {app.name}"

    after = {
        "apps": [] if data.mode == "hard" else [a.id for a in apps],
        "policies": [] if data.mode == "hard" else [p.id for p in policies],
        "at": now.isoformat(),
    }
    request_record = OffboardingRequest(
        id=str(uuid.uuid4()), tenant_id=tid, requested_by=getattr(request.state, "user_id", None),
        mode=data.mode, status=status, before_hash=before_hash,
        after_hash=hashlib.sha256(json.dumps(after, sort_keys=True).encode()).hexdigest(),
        requested_at=now, hard_delete_at=hard_delete_at,
        completed_at=now if data.mode == "soft" else None,
    )
    db.add(request_record)
    db.flush()
    _audit(db, tid, getattr(request.state, "user_id", None), request_record.id,
           {"mode": data.mode, "before_hash": before_hash, "hard_delete_at": hard_delete_at.isoformat()})
    db.commit()
    return {
        "id": request_record.id,
        "tenant_id": tid,
        "mode": data.mode,
        "before_hash": before_hash,
        "after_hash": request_record.after_hash,
        "status": status.lower(),
        "hard_delete_at": hard_delete_at.isoformat(),
    }


@router.get("/status")
async def offboarding_status(request: Request, db: Session = Depends(db_with_tenant)):
    tid = tenant_id(request)
    record = db.query(OffboardingRequest).filter(
        OffboardingRequest.tenant_id == tid
    ).order_by(OffboardingRequest.requested_at.desc()).first()
    if not record:
        return {"tenant_id": tid, "status": "active"}
    return {
        "id": record.id, "tenant_id": tid, "mode": record.mode, "status": record.status.lower(),
        "hard_delete_at": record.hard_delete_at.isoformat() if record.hard_delete_at else None,
        "before_hash": record.before_hash, "after_hash": record.after_hash,
    }
