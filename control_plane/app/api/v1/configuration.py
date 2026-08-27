from __future__ import annotations

import json
import os
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from control_plane.app.api.deps import db_with_tenant, tenant_id
from control_plane.app.infrastructure.db.models import ConfigurationEntry

router = APIRouter(prefix="/configuration", tags=["configuration"])

DEFAULT_CONFIG: dict[str, Any] = {
    "environment": os.getenv("ENVIRONMENT", "development"),
    "rate_limit": int(os.getenv("RATE_LIMIT", "60")),
    "jwt_expiry_minutes": 15,
    "mfa_enabled": True,
    "waf_enabled": True,
    "threat_intel_enabled": True,
    "log_level": os.getenv("LOG_LEVEL", "info"),
    "version": "0.1.0",
}
ALLOWED_KEYS = frozenset(DEFAULT_CONFIG)


class ConfigUpdate(BaseModel):
    key: str = Field(min_length=1, max_length=128)
    value: Any


def _admin(request: Request) -> str:
    if not getattr(request.state, "is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return tenant_id(request)


@router.get("/")
@router.get("")
async def get_configuration(request: Request, db: Session = Depends(db_with_tenant)):
    tid = tenant_id(request)
    values = dict(DEFAULT_CONFIG)
    entries = db.query(ConfigurationEntry).filter(ConfigurationEntry.tenant_id == tid).all()
    for entry in entries:
        try:
            values[entry.key] = json.loads(entry.value)
        except json.JSONDecodeError:
            values[entry.key] = entry.value
    return values


@router.put("/")
@router.put("")
async def update_configuration(data: ConfigUpdate, request: Request, db: Session = Depends(db_with_tenant)):
    tid = _admin(request)
    if data.key not in ALLOWED_KEYS:
        raise HTTPException(status_code=404, detail="Config key not found")
    entry = db.query(ConfigurationEntry).filter(
        ConfigurationEntry.tenant_id == tid, ConfigurationEntry.key == data.key
    ).first()
    now = datetime.now(UTC)
    encoded = json.dumps(data.value, sort_keys=True)
    if entry:
        entry.value = encoded
        entry.updated_by = getattr(request.state, "user_id", None)
        entry.updated_at = now
    else:
        entry = ConfigurationEntry(
            id=str(uuid.uuid4()), tenant_id=tid, key=data.key, value=encoded,
            updated_by=getattr(request.state, "user_id", None), updated_at=now,
        )
        db.add(entry)
    db.commit()
    return {"key": entry.key, "value": data.value, "updated": True, "updated_at": now.isoformat()}
