from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from control_plane.app.api.deps import db_with_tenant, tenant_id
from control_plane.app.domain.compliance.applicability import ApplicabilityEngine
from control_plane.app.infrastructure.db.models import ApplicabilityDecision

router = APIRouter(prefix="/compliance", tags=["compliance"])
_engine = ApplicabilityEngine()


class ApplicabilityRequest(BaseModel):
    customer_type: str = Field(min_length=1, max_length=64)
    industry: str = Field(min_length=1, max_length=128)
    data_type: str = Field(min_length=1, max_length=128)
    region: str = Field(min_length=1, max_length=64)


def _admin(request: Request) -> str:
    if not getattr(request.state, "is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return tenant_id(request)


@router.post("/applicability/evaluate")
async def evaluate_applicability(
    data: ApplicabilityRequest,
    request: Request,
    db: Session = Depends(db_with_tenant),
):
    tid = _admin(request)
    result = _engine.determine_applicability(**data.model_dump())
    result["responsibility"] = {
        framework["framework"]: {"owner": "SentinelLayer", "customer_responsibility": "Provide applicable scope and evidence"}
        for framework in result["applicable_frameworks"]
    }
    record = ApplicabilityDecision(
        id=str(uuid.uuid4()), tenant_id=tid, result=json.dumps(result, sort_keys=True),
        evaluated_by=getattr(request.state, "user_id", None), evaluated_at=datetime.now(UTC), **data.model_dump(),
    )
    db.add(record)
    db.commit()
    return {"id": record.id, "tenant_id": tid, **result, "evaluated_at": record.evaluated_at.isoformat()}


@router.get("/applicability/latest")
async def latest_applicability(request: Request, db: Session = Depends(db_with_tenant)):
    record = db.query(ApplicabilityDecision).filter(
        ApplicabilityDecision.tenant_id == tenant_id(request)
    ).order_by(ApplicabilityDecision.evaluated_at.desc()).first()
    if not record:
        raise HTTPException(status_code=404, detail="No applicability decision recorded")
    return {"id": record.id, "tenant_id": record.tenant_id, **json.loads(record.result),
            "evaluated_at": record.evaluated_at.isoformat()}


@router.get("/applicability")
async def list_applicability(request: Request, db: Session = Depends(db_with_tenant)):
    records = db.query(ApplicabilityDecision).filter(
        ApplicabilityDecision.tenant_id == tenant_id(request)
    ).order_by(ApplicabilityDecision.evaluated_at.desc()).limit(100).all()
    return [{"id": record.id, "tenant_id": record.tenant_id, "customer_type": record.customer_type,
             "industry": record.industry, "data_type": record.data_type, "region": record.region,
             "applicable_frameworks": json.loads(record.result).get("applicable_frameworks", []),
             "evaluated_at": record.evaluated_at.isoformat()} for record in records]
