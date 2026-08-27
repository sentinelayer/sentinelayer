from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from control_plane.app.api.deps import db_with_tenant, tenant_id
from control_plane.app.infrastructure.db.models import RuntimeEvent, User

router = APIRouter(prefix="/user-risk", tags=["user-risk"])


def _event_user_id(event: RuntimeEvent) -> str | None:
    try:
        data = json.loads(event.data or "{}")
    except json.JSONDecodeError:
        return None
    return str(data.get("user_id")) if data.get("user_id") else None


def _risk_rows(request: Request, db: Session, hours: int) -> list[dict[str, Any]]:
    tid = tenant_id(request)
    users = db.query(User).filter(User.tenant_id == tid).order_by(User.email.asc()).all()
    cutoff = datetime.now(UTC) - timedelta(hours=hours)
    events = db.query(RuntimeEvent).filter(
        RuntimeEvent.tenant_id == tid, RuntimeEvent.occurred_at >= cutoff
    ).all()
    by_user: dict[str, list[RuntimeEvent]] = {}
    for event in events:
        user_id = _event_user_id(event)
        if user_id:
            by_user.setdefault(user_id, []).append(event)
    rows = []
    for user in users:
        user_events = by_user.get(user.id, [])
        scores = [event.risk_score for event in user_events if event.risk_score is not None]
        score = max(scores, default=0)
        failures = sum(event.event_type in {"auth.failure", "authentication.failure"} for event in user_events)
        suspicious_ip = any(event.event_type in {"suspicious.ip", "ip.reputation.hit"} for event in user_events)
        unusual_time = any(event.event_type == "unusual.time" for event in user_events)
        status = "blocked" if score >= 80 else "suspicious" if score >= 50 or suspicious_ip else "active"
        latest = max((event.occurred_at for event in user_events), default=None)
        rows.append({
            "user_id": user.id, "email": user.email, "risk_score": score, "status": status,
            "last_activity": latest.isoformat() if latest else None,
            "factors": {"failed_attempts": failures, "suspicious_ip": suspicious_ip, "unusual_time": unusual_time},
        })
    return rows


@router.get("/")
@router.get("")
async def get_user_risk(
    request: Request,
    hours: int = Query(default=24, ge=1, le=168),
    db: Session = Depends(db_with_tenant),
):
    return _risk_rows(request, db, hours)


@router.get("/{user_id}")
async def get_user_risk_detail(
    user_id: str,
    request: Request,
    hours: int = Query(default=24, ge=1, le=168),
    db: Session = Depends(db_with_tenant),
):
    rows = _risk_rows(request, db, hours)
    for row in rows:
        if row["user_id"] == user_id:
            return row
    raise HTTPException(status_code=404, detail="User not found for tenant")
