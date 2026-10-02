"""Append events in the caller's transaction; never commit before domain state."""
import json
import uuid
from datetime import UTC, datetime

from sqlalchemy import text
from control_plane.app.infrastructure.db.models import RuntimeEvent


def append_event(db, tenant_id, event_type, *, source="control-plane", data=None,
                 severity=None, risk_score=None, outcome=None):
    db.execute(text("""INSERT INTO tenant_event_offsets (tenant_id,last_sequence)
        VALUES (:tenant,0) ON CONFLICT (tenant_id) DO NOTHING"""), {"tenant": tenant_id})
    # UPDATE acquires a per-tenant row lock until commit. A later sequence cannot
    # commit first, which prevents replay clients from skipping in-flight events.
    sequence = db.scalar(text("""UPDATE tenant_event_offsets SET last_sequence=last_sequence+1
        WHERE tenant_id=:tenant RETURNING last_sequence"""), {"tenant": tenant_id})
    event = RuntimeEvent(id=str(uuid.uuid4()), tenant_id=tenant_id, sequence=sequence,
                         event_type=event_type, source=source, data=json.dumps(data or {}, sort_keys=True),
                         severity=severity, risk_score=risk_score, outcome=outcome,
                         occurred_at=datetime.now(UTC))
    db.add(event)
    db.flush()
    return event
