from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from control_plane.app.api.deps import db_with_tenant, tenant_id
from control_plane.app.infrastructure.db.models import RuntimeEvent

router = APIRouter(prefix="/sla", tags=["sla"])


@router.get("/report")
async def sla_report(
    request: Request,
    period_hours: int = Query(default=24, ge=1, le=168),
    db: Session = Depends(db_with_tenant),
):
    tid = tenant_id(request)
    cutoff = datetime.now(UTC) - timedelta(hours=period_hours)
    events = db.query(RuntimeEvent).filter(
        RuntimeEvent.tenant_id == tid, RuntimeEvent.occurred_at >= cutoff
    ).all()
    pass_count = sum(event.outcome in {"success", "allowed", "pass", "ok"} for event in events)
    fail_count = sum(event.outcome in {"failure", "failed", "error", "timeout"} for event in events)
    classified = pass_count + fail_count
    return {
        "compliance_rate": round((pass_count / classified) * 100, 2) if classified else None,
        "period_hours": period_hours,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "sample_count": len(events),
        "classified_count": classified,
        "generated_at": datetime.now(UTC).isoformat(),
    }
