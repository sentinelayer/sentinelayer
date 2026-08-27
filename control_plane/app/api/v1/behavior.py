from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from control_plane.app.api.deps import db_with_tenant, tenant_id
from control_plane.app.infrastructure.db.models import BehaviorBaselineRecord

router = APIRouter(prefix="/behavior", tags=["behavior"])


class BaselineCreate(BaseModel):
    baseline_key: str = Field(min_length=1, max_length=256)
    baseline_type: str = Field(min_length=1, max_length=64)
    stats: dict[str, float | int | str] = Field(default_factory=dict)


def _admin(request: Request) -> str:
    if not getattr(request.state, "is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return tenant_id(request)


def _serialize(row: BehaviorBaselineRecord) -> dict:
    return {"id": row.id, "tenant_id": row.tenant_id, "baseline_key": row.baseline_key,
            "baseline_type": row.baseline_type, "version": row.version,
            "stats": json.loads(row.stats or "{}"), "status": row.status,
            "created_at": row.created_at.isoformat(), "updated_at": row.updated_at.isoformat()}


@router.post("/baselines")
async def create_baseline(data: BaselineCreate, request: Request, db: Session = Depends(db_with_tenant)):
    tid = _admin(request)
    latest = db.query(BehaviorBaselineRecord).filter(
        BehaviorBaselineRecord.tenant_id == tid,
        BehaviorBaselineRecord.baseline_key == data.baseline_key,
        BehaviorBaselineRecord.baseline_type == data.baseline_type,
    ).order_by(BehaviorBaselineRecord.version.desc()).first()
    now = datetime.now(UTC)
    row = BehaviorBaselineRecord(
        id=str(uuid.uuid4()), tenant_id=tid, baseline_key=data.baseline_key,
        baseline_type=data.baseline_type, version=(latest.version + 1 if latest else 1),
        stats=json.dumps(data.stats, sort_keys=True), status="active", created_at=now, updated_at=now,
    )
    if latest:
        latest.status = "superseded"
        latest.updated_at = now
    db.add(row)
    db.commit()
    db.refresh(row)
    return _serialize(row)


@router.get("/baselines")
async def list_baselines(request: Request, db: Session = Depends(db_with_tenant)):
    rows = db.query(BehaviorBaselineRecord).filter(
        BehaviorBaselineRecord.tenant_id == tenant_id(request)
    ).order_by(BehaviorBaselineRecord.baseline_key.asc(), BehaviorBaselineRecord.version.desc()).all()
    return [_serialize(row) for row in rows]


@router.post("/baselines/{baseline_id}/rollback")
async def rollback_baseline(baseline_id: str, request: Request, db: Session = Depends(db_with_tenant)):
    tid = _admin(request)
    target = db.query(BehaviorBaselineRecord).filter(
        BehaviorBaselineRecord.id == baseline_id, BehaviorBaselineRecord.tenant_id == tid
    ).first()
    if not target:
        raise HTTPException(status_code=404, detail="Baseline not found")
    now = datetime.now(UTC)
    rows = db.query(BehaviorBaselineRecord).filter(
        BehaviorBaselineRecord.tenant_id == tid,
        BehaviorBaselineRecord.baseline_key == target.baseline_key,
        BehaviorBaselineRecord.baseline_type == target.baseline_type,
    ).all()
    for row in rows:
        row.status = "active" if row.id == target.id else "rolled_back"
        row.updated_at = now
    db.commit()
    db.refresh(target)
    return _serialize(target)
