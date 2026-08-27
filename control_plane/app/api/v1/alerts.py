from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from control_plane.app.api.deps import db_with_tenant, tenant_id
from control_plane.app.infrastructure.db.models import Alert

router = APIRouter(prefix="/alerts", tags=["alerts"])


class AlertCreate(BaseModel):
    severity: str = Field(min_length=1, max_length=16)
    message: str = Field(min_length=1, max_length=4000)
    source: str = Field(default="system", min_length=1, max_length=128)


@router.post("/")
@router.post("")
async def create_alert(data: AlertCreate, request: Request, db: Session = Depends(db_with_tenant)):
    alert = Alert(
        id=__import__("uuid").uuid4().hex, tenant_id=tenant_id(request), severity=data.severity,
        message=data.message, source=data.source, status="active", created_at=datetime.now(UTC),
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return _serialize(alert)


def _serialize(alert: Alert) -> dict[str, Any]:
    return {
        "id": alert.id, "tenant_id": alert.tenant_id, "severity": alert.severity,
        "message": alert.message, "source": alert.source, "status": alert.status,
        "created_at": alert.created_at.isoformat(),
        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
        "resolved_by": alert.resolved_by,
    }


@router.get("/")
@router.get("")
async def list_alerts(
    request: Request,
    status: str | None = Query(default=None, max_length=16),
    db: Session = Depends(db_with_tenant),
):
    query = db.query(Alert).filter(Alert.tenant_id == tenant_id(request))
    if status:
        query = query.filter(Alert.status == status)
    return [_serialize(alert) for alert in query.order_by(Alert.created_at.desc()).all()]


@router.post("/{id}/resolve")
async def resolve_alert(id: str, request: Request, db: Session = Depends(db_with_tenant)):
    alert = db.query(Alert).filter(Alert.id == id, Alert.tenant_id == tenant_id(request)).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if alert.status == "resolved":
        raise HTTPException(status_code=409, detail="Alert already resolved")
    alert.status = "resolved"
    alert.resolved_at = datetime.now(UTC)
    alert.resolved_by = getattr(request.state, "user_id", None)
    db.commit()
    db.refresh(alert)
    return _serialize(alert)
