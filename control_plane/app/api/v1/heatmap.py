from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from control_plane.app.api.deps import db_with_tenant, tenant_id
from control_plane.app.infrastructure.db.models import RuntimeEvent

router = APIRouter(prefix="/heatmap", tags=["heatmap"])


@router.get("/")
@router.get("")
async def get_heatmap(
    request: Request,
    hours: int = Query(default=24, ge=1, le=168),
    db: Session = Depends(db_with_tenant),
) -> list[dict[str, Any]]:
    tid = tenant_id(request)
    cutoff = datetime.now(UTC) - timedelta(hours=hours)
    events = db.query(RuntimeEvent).filter(
        RuntimeEvent.tenant_id == tid, RuntimeEvent.occurred_at >= cutoff
    ).all()
    grouped: dict[str, list[RuntimeEvent]] = defaultdict(list)
    for event in events:
        try:
            data = json.loads(event.data or "{}")
        except json.JSONDecodeError:
            data = {}
        endpoint = data.get("endpoint") or data.get("path") or "unknown"
        grouped[str(endpoint)].append(event)
    cells = []
    for endpoint, endpoint_events in sorted(grouped.items()):
        scores = [event.risk_score for event in endpoint_events if event.risk_score is not None]
        blocks = sum(event.outcome in {"blocked", "block"} or event.event_type in {"waf.block", "waf.blocked"}
                     for event in endpoint_events)
        cells.append({
            "endpoint": endpoint,
            "risk": max(scores, default=0),
            "requests": len(endpoint_events),
            "blocks": blocks,
            "window_hours": hours,
        })
    return cells
