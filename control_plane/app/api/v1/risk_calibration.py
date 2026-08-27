from __future__ import annotations

from datetime import UTC, datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from control_plane.app.api.deps import db_with_tenant, tenant_id
from control_plane.app.infrastructure.db.models import RiskCalibrationRecord

router = APIRouter(prefix="/risk", tags=["risk"])


class CalibrationCreate(BaseModel):
    factor: int = Field(default=100, ge=0, le=200)
    dataset_hash: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-fA-F]{64}$")
    sample_count: int = Field(default=0, ge=0)
    fp_rate: int | None = Field(default=None, ge=0, le=100)
    fn_rate: int | None = Field(default=None, ge=0, le=100)


def _admin(request: Request) -> str:
    if not getattr(request.state, "is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return tenant_id(request)


def _serialize(row: RiskCalibrationRecord) -> dict:
    return {"id": row.id, "tenant_id": row.tenant_id, "version": row.version, "factor": row.factor,
            "dataset_hash": row.dataset_hash, "sample_count": row.sample_count, "fp_rate": row.fp_rate,
            "fn_rate": row.fn_rate, "status": row.status, "created_at": row.created_at.isoformat()}


@router.post("/calibrations")
async def create_calibration(data: CalibrationCreate, request: Request, db: Session = Depends(db_with_tenant)):
    tid = _admin(request)
    latest = db.query(RiskCalibrationRecord).filter(
        RiskCalibrationRecord.tenant_id == tid
    ).order_by(RiskCalibrationRecord.version.desc()).first()
    now = datetime.now(UTC)
    if latest:
        latest.status = "superseded"
    row = RiskCalibrationRecord(
        id=str(uuid.uuid4()), tenant_id=tid, version=(latest.version + 1 if latest else 1),
        factor=data.factor, dataset_hash=data.dataset_hash.lower(), sample_count=data.sample_count,
        fp_rate=data.fp_rate, fn_rate=data.fn_rate, status="active", created_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _serialize(row)


@router.get("/calibrations")
async def list_calibrations(request: Request, db: Session = Depends(db_with_tenant)):
    rows = db.query(RiskCalibrationRecord).filter(
        RiskCalibrationRecord.tenant_id == tenant_id(request)
    ).order_by(RiskCalibrationRecord.version.desc()).all()
    return [_serialize(row) for row in rows]


@router.post("/calibrations/{calibration_id}/activate")
async def activate_calibration(calibration_id: str, request: Request, db: Session = Depends(db_with_tenant)):
    tid = _admin(request)
    target = db.query(RiskCalibrationRecord).filter(
        RiskCalibrationRecord.id == calibration_id, RiskCalibrationRecord.tenant_id == tid
    ).first()
    if not target:
        raise HTTPException(status_code=404, detail="Calibration not found")
    rows = db.query(RiskCalibrationRecord).filter(RiskCalibrationRecord.tenant_id == tid).all()
    for row in rows:
        row.status = "active" if row.id == target.id else "superseded"
    db.commit()
    db.refresh(target)
    return _serialize(target)
