from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from control_plane.app.api.deps import db_with_tenant, tenant_id
from control_plane.app.infrastructure.db.models import RuntimeEvent

router = APIRouter(prefix="/explainability", tags=["explainability"])


def _serialize(event: RuntimeEvent) -> dict[str, Any]:
    try:
        data = json.loads(event.data or "{}")
    except json.JSONDecodeError:
        data = {}
    action = data.get("action") or data.get("decision") or event.outcome or "unknown"
    return {
        "id": event.id,
        "action": action,
        "reason": data.get("reason") or data.get("explanation"),
        "who": data.get("actor") or event.source,
        "when": event.occurred_at.isoformat(),
        "timestamp": event.occurred_at.isoformat(),
        "score": event.risk_score,
        "risk_score": event.risk_score,
        "factors": data.get("factors", []),
        "data": data,
    }


def _query(request: Request, db: Session, decision_id: str | None = None, limit: int = 100):
    query = db.query(RuntimeEvent).filter(
        RuntimeEvent.tenant_id == tenant_id(request), RuntimeEvent.event_type.like("decision.%")
    )
    if decision_id:
        query = query.filter(RuntimeEvent.id == decision_id)
    return query.order_by(RuntimeEvent.occurred_at.desc()).limit(limit).all()


@router.get("/latest")
async def get_latest_explainability(request: Request, db: Session = Depends(db_with_tenant)):
    events = _query(request, db, limit=1)
    if not events:
        raise HTTPException(status_code=404, detail="No decisions recorded yet")
    return _serialize(events[0])


@router.get("/")
@router.get("")
async def get_explainability(
    request: Request,
    decision_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(db_with_tenant),
):
    events = _query(request, db, decision_id=decision_id, limit=limit)
    if decision_id and not events:
        raise HTTPException(status_code=404, detail="Decision not found")
    return [_serialize(event) for event in events]


@router.get("/decision/{decision_id}")
async def get_decision_explainability(decision_id: str, request: Request, db: Session = Depends(db_with_tenant)):
    events = _query(request, db, decision_id=decision_id, limit=1)
    if not events:
        raise HTTPException(status_code=404, detail="Decision not found")
    return _serialize(events[0])
