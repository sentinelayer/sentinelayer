from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from control_plane.app.api.deps import db_with_tenant, tenant_id
from control_plane.app.infrastructure.db.models import (
    Alert,
    AuditEvent,
    LegalHoldRecord,
    PrivacyExportRequest,
    RuntimeEvent,
    User,
)

router = APIRouter(prefix="/privacy", tags=["privacy"])


class LegalHoldCreate(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)
    scope: dict[str, str] = Field(default_factory=dict)


def _admin(request: Request) -> tuple[str, str | None]:
    if not getattr(request.state, "is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return tenant_id(request), getattr(request.state, "user_id", None)


def _hold(row: LegalHoldRecord) -> dict:
    return {"id": row.id, "tenant_id": row.tenant_id, "reason": row.reason,
            "scope": json.loads(row.scope or "{}"), "status": row.status,
            "created_by": row.created_by, "created_at": row.created_at.isoformat(),
            "released_at": row.released_at.isoformat() if row.released_at else None,
            "released_by": row.released_by}


@router.post("/legal-holds")
async def create_legal_hold(data: LegalHoldCreate, request: Request, db: Session = Depends(db_with_tenant)):
    tid, actor = _admin(request)
    row = LegalHoldRecord(id=str(uuid.uuid4()), tenant_id=tid, reason=data.reason.strip(),
                          scope=json.dumps(data.scope, sort_keys=True), status="active", created_by=actor,
                          created_at=datetime.now(UTC))
    db.add(row)
    db.commit()
    db.refresh(row)
    return _hold(row)


@router.get("/legal-holds")
async def list_legal_holds(request: Request, db: Session = Depends(db_with_tenant)):
    rows = db.query(LegalHoldRecord).filter(LegalHoldRecord.tenant_id == tenant_id(request)).order_by(
        LegalHoldRecord.created_at.desc()).all()
    return [_hold(row) for row in rows]


@router.post("/legal-holds/{hold_id}/release")
async def release_legal_hold(hold_id: str, request: Request, db: Session = Depends(db_with_tenant)):
    tid, actor = _admin(request)
    row = db.query(LegalHoldRecord).filter(LegalHoldRecord.id == hold_id, LegalHoldRecord.tenant_id == tid).first()
    if not row:
        raise HTTPException(status_code=404, detail="Legal hold not found")
    if row.status != "active":
        raise HTTPException(status_code=409, detail="Legal hold is already released")
    row.status = "released"
    row.released_at = datetime.now(UTC)
    row.released_by = actor
    db.commit()
    return _hold(row)


@router.post("/exports")
async def create_export(request: Request, db: Session = Depends(db_with_tenant)):
    tid, actor = _admin(request)
    export = PrivacyExportRequest(id=str(uuid.uuid4()), tenant_id=tid, requested_by=actor,
                                  status="PROCESSING", created_at=datetime.now(UTC))
    db.add(export)
    db.flush()
    # Export only tenant-scoped metadata; secrets, password hashes, and encrypted material are excluded.
    snapshot = {
        "tenant_id": tid,
        "users": [{"id": row.id, "email": row.email, "full_name": row.full_name,
                    "is_active": row.is_active, "is_admin": row.is_admin, "created_at": row.created_at.isoformat()}
                   for row in db.query(User).filter(User.tenant_id == tid).all()],
        "events": [{"id": row.id, "event_type": row.event_type, "source": row.source,
                    "severity": row.severity, "risk_score": row.risk_score, "outcome": row.outcome,
                    "occurred_at": row.occurred_at.isoformat()} for row in db.query(RuntimeEvent).filter(RuntimeEvent.tenant_id == tid).all()],
        "alerts": [{"id": row.id, "severity": row.severity, "message": row.message,
                    "status": row.status, "created_at": row.created_at.isoformat()} for row in db.query(Alert).filter(Alert.tenant_id == tid).all()],
        "audit_event_count": db.query(AuditEvent).filter(AuditEvent.tenant_id == tid).count(),
    }
    raw = json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
    directory = Path("/tmp/sentinelayer-privacy-exports")
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = directory / f"{export.id}.json"
    path.write_bytes(raw)
    path.chmod(0o600)
    export.status = "COMPLETED"
    export.artifact_path = str(path)
    export.artifact_hash = hashlib.sha256(raw).hexdigest()
    export.completed_at = datetime.now(UTC)
    db.commit()
    return {"id": export.id, "status": export.status, "artifact_hash": export.artifact_hash,
            "record_count": len(snapshot["users"]) + len(snapshot["events"]) + len(snapshot["alerts"])}


@router.get("/exports")
async def list_exports(request: Request, db: Session = Depends(db_with_tenant)):
    rows = db.query(PrivacyExportRequest).filter(
        PrivacyExportRequest.tenant_id == tenant_id(request)
    ).order_by(PrivacyExportRequest.created_at.desc()).all()
    return [{"id": row.id, "status": row.status, "artifact_hash": row.artifact_hash,
             "created_at": row.created_at.isoformat(), "completed_at": row.completed_at.isoformat() if row.completed_at else None}
            for row in rows]
