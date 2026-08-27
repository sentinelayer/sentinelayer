from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session

from control_plane.app.api.deps import db_with_tenant, tenant_id
from control_plane.app.infrastructure.db.models import RuntimeEvent

router = APIRouter(prefix="/metrics", tags=["metrics"])
start_time = time.time()


def _status(value: int, warning_at: int = 1) -> str:
    return "warning" if value >= warning_at else "good"


@router.get("/security")
async def security_metrics(
    request: Request,
    hours: int = Query(default=24, ge=1, le=168),
    db: Session = Depends(db_with_tenant),
):
    tid = tenant_id(request)
    cutoff = datetime.now(UTC) - timedelta(hours=hours)
    base = db.query(RuntimeEvent).filter(RuntimeEvent.tenant_id == tid, RuntimeEvent.occurred_at >= cutoff)
    waf_blocks = base.filter(or_(
        RuntimeEvent.outcome.in_(["blocked", "block"]),
        RuntimeEvent.event_type.in_(["waf.block", "waf.blocked"]),
        RuntimeEvent.event_type.like("waf.%"),
    )).count()
    active_threats = base.filter(RuntimeEvent.severity.in_(["high", "critical"])).count()
    auth_failures = base.filter(RuntimeEvent.event_type.in_(["auth.failure", "authentication.failure"])).count()
    total_events = base.count()
    uptime = int(time.time() - start_time)
    return [
        {"name": "WAF Blocks", "value": waf_blocks, "status": _status(waf_blocks)},
        {"name": "Active Threats", "value": active_threats, "status": _status(active_threats)},
        {"name": "Auth Failures", "value": auth_failures, "status": _status(auth_failures)},
        {"name": "Events", "value": total_events, "status": "good"},
        {"name": "Window", "value": f"{hours}h", "status": "good"},
        {"name": "Uptime", "value": f"{uptime}s", "status": "good"},
    ]
