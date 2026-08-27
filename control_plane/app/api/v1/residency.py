from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from control_plane.app.api.deps import db_with_tenant, tenant_id
from control_plane.app.infrastructure.db.models import ResidencyRuleRecord

router = APIRouter(prefix="/residency", tags=["residency"])


class ResidencyRule(BaseModel):
    data_type: str = Field(min_length=1, max_length=128)
    primary_region: str = Field(min_length=1, max_length=64)
    backup_region: str = Field(min_length=1, max_length=64)


def _admin(request: Request) -> str:
    if not getattr(request.state, "is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return tenant_id(request)


@router.post("/rules")
async def create_rule(rule: ResidencyRule, request: Request, db: Session = Depends(db_with_tenant)):
    tid = _admin(request)
    record = ResidencyRuleRecord(
        id=__import__("uuid").uuid4().hex, tenant_id=tid, data_type=rule.data_type,
        primary_region=rule.primary_region, backup_region=rule.backup_region,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"id": record.id, "tenant_id": tid, **rule.model_dump()}


@router.get("/rules")
async def list_rules(request: Request, db: Session = Depends(db_with_tenant)):
    tid = tenant_id(request)
    records = db.query(ResidencyRuleRecord).filter(ResidencyRuleRecord.tenant_id == tid).order_by(
        ResidencyRuleRecord.data_type.asc(), ResidencyRuleRecord.created_at.desc()).all()
    return [{"id": r.id, "tenant_id": tid, "data_type": r.data_type,
             "primary_region": r.primary_region, "backup_region": r.backup_region} for r in records]


@router.get("/enforce/{data_type}/{region}")
async def enforce_residency(data_type: str, region: str, request: Request, db: Session = Depends(db_with_tenant)):
    tid = tenant_id(request)
    rule = db.query(ResidencyRuleRecord).filter(
        ResidencyRuleRecord.tenant_id == tid, ResidencyRuleRecord.data_type == data_type
    ).order_by(ResidencyRuleRecord.created_at.desc()).first()
    if not rule:
        return {"allowed": True, "region": region, "rule": None}
    if region == rule.primary_region or region == rule.backup_region:
        return {"allowed": True, "region": region, "required_region": rule.primary_region}
    return {"allowed": False, "region": region, "required_region": rule.primary_region,
            "backup_region": rule.backup_region}
