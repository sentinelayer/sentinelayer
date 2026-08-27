import json
from datetime import UTC, datetime

from control_plane.app.infrastructure.db.models import Evidence
from control_plane.app.infrastructure.db.session import SessionLocal


def expire_old_evidence() -> dict[str, int]:
    """Expire only evidence that is explicitly past its validity boundary."""
    db = SessionLocal()
    try:
        now = datetime.now(UTC)
        candidates = (
            db.query(Evidence)
            .filter(Evidence.status.in_(["CREATED", "VERIFIED", "VALID"]))
            .all()
        )
        expired_count = 0
        for evidence in candidates:
            valid_until = evidence.valid_until
            if valid_until is None:
                continue
            if valid_until.tzinfo is None:
                valid_until = valid_until.replace(tzinfo=UTC)
            if valid_until >= now:
                continue
            chain = json.loads(evidence.chain_of_custody or "[]")
            chain.append(
                {
                    "action": "EXPIRED",
                    "actor": "maintenance-worker",
                    "at": now.isoformat(),
                    "reason": "valid_until elapsed",
                }
            )
            evidence.status = "EXPIRED"
            evidence.expired_at = now
            evidence.chain_of_custody = json.dumps(chain)
            expired_count += 1
        db.commit()
        return {"expired": expired_count}
    finally:
        db.close()
