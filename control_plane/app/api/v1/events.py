from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from control_plane.app.api.deps import db_with_tenant, tenant_id
from control_plane.app.infrastructure.db.models import RuntimeEvent

router = APIRouter(prefix="/events", tags=["events"])


class EventCreate(BaseModel):
    event_type: str = Field(min_length=1, max_length=128)
    source: str = Field(default="system", min_length=1, max_length=128)
    data: dict[str, Any] = Field(default_factory=dict)
    severity: str | None = Field(default=None, max_length=16)
    risk_score: int | None = Field(default=None, ge=0, le=100)
    outcome: str | None = Field(default=None, max_length=32)


def _serialize(event: RuntimeEvent) -> dict[str, Any]:
    try:
        data = json.loads(event.data or "{}")
    except json.JSONDecodeError:
        data = {"raw": event.data}
    return {
        "id": event.id,
        "tenant_id": event.tenant_id,
        "type": event.event_type,
        "source": event.source,
        "data": data,
        "severity": event.severity,
        "risk_score": event.risk_score,
        "outcome": event.outcome,
        "timestamp": event.occurred_at.isoformat(),
    }


@router.get("/")
@router.get("")
async def get_events(
    request: Request,
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(db_with_tenant),
):
    tid = tenant_id(request)
    events = db.query(RuntimeEvent).filter(RuntimeEvent.tenant_id == tid).order_by(
        RuntimeEvent.occurred_at.desc(), RuntimeEvent.id.desc()).limit(limit).all()
    return [_serialize(event) for event in events]


@router.post("/")
@router.post("")
async def create_event(body: EventCreate, request: Request, db: Session = Depends(db_with_tenant)):
    tid = tenant_id(request)
    event = RuntimeEvent(
        id=str(uuid.uuid4()), tenant_id=tid, event_type=body.event_type, source=body.source,
        data=json.dumps(body.data, sort_keys=True), severity=body.severity,
        risk_score=body.risk_score, outcome=body.outcome, occurred_at=datetime.now(UTC),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return _serialize(event)
