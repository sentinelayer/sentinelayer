"""Tenant-safe threat-intelligence indicators with explicit freshness and TTL."""
from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from control_plane.app.api.deps import db_with_tenant, tenant_id
from control_plane.app.infrastructure.db.models import ThreatIntelIndicator

router = APIRouter(prefix="/threat-intel", tags=["threat-intel"])


class IndicatorCreate(BaseModel):
    indicator_type: str = Field(min_length=1, max_length=32)
    value: str = Field(min_length=1, max_length=512)
    severity: str = Field(default="medium", max_length=16)
    source: str = Field(default="internal", min_length=1, max_length=128)
    tags: list[str] = Field(default_factory=list)
    confidence: int = Field(default=50, ge=0, le=100)
    reliability: int = Field(default=50, ge=0, le=100)
    ttl_hours: int | None = Field(default=None, ge=1, le=8760)


def _serialize(indicator: ThreatIntelIndicator) -> dict[str, Any]:
    try:
        tags = json.loads(indicator.tags or "[]")
    except json.JSONDecodeError:
        tags = []
    return {
        "id": indicator.id,
        "tenant_id": indicator.tenant_id,
        "type": indicator.indicator_type,
        "value": indicator.value,
        "severity": indicator.severity,
        "source": indicator.source,
        "tags": tags,
        "confidence": indicator.confidence,
        "reliability": indicator.reliability,
        "first_seen": indicator.first_seen.isoformat(),
        "last_seen": indicator.last_seen.isoformat(),
        "expires_at": indicator.expires_at.isoformat() if indicator.expires_at else None,
    }


def _seed_global_feed(db: Session, tenant: str) -> None:
    if db.query(ThreatIntelIndicator).filter(ThreatIntelIndicator.tenant_id == tenant).count():
        return
    now = datetime.now(UTC)
    seed = [
        ("ip", "203.0.113.50", "high", ["scanner"]),
        ("ip", "198.51.100.23", "medium", ["bruteforce"]),
        ("ua", "sqlmap", "high", ["sqli-tool"]),
        ("path", "/.env", "medium", ["secret-scan"]),
    ]
    for indicator_type, value, severity, tags in seed:
        db.add(ThreatIntelIndicator(
            id=f"internal-{uuid.uuid4()}", tenant_id=tenant, indicator_type=indicator_type,
            value=value, severity=severity, source="internal-curated", tags=json.dumps(tags),
            confidence=80, reliability=80, first_seen=now, last_seen=now, created_at=now, updated_at=now,
        ))
    db.flush()


@router.get("/indicators")
async def list_indicators(
    request: Request,
    indicator_type: str | None = Query(default=None, max_length=32),
    db: Session = Depends(db_with_tenant),
):
    tid = tenant_id(request)
    _seed_global_feed(db, tid)
    now = datetime.now(UTC)
    query = db.query(ThreatIntelIndicator).filter(
        ThreatIntelIndicator.tenant_id == tid,
        or_(ThreatIntelIndicator.expires_at.is_(None), ThreatIntelIndicator.expires_at > now),
    )
    if indicator_type:
        query = query.filter(ThreatIntelIndicator.indicator_type == indicator_type)
    indicators = query.order_by(ThreatIntelIndicator.last_seen.desc()).all()
    db.commit()
    return {
        "count": len(indicators),
        "updated_at": now.isoformat(),
        "indicators": [_serialize(indicator) for indicator in indicators],
    }


@router.post("/indicators")
async def create_indicator(data: IndicatorCreate, request: Request, db: Session = Depends(db_with_tenant)):
    tid = tenant_id(request)
    now = datetime.now(UTC)
    indicator = ThreatIntelIndicator(
        id=str(uuid.uuid4()), tenant_id=tid, indicator_type=data.indicator_type, value=data.value,
        severity=data.severity, source=data.source, tags=json.dumps(data.tags), confidence=data.confidence,
        reliability=data.reliability, first_seen=now, last_seen=now,
        expires_at=now + timedelta(hours=data.ttl_hours) if data.ttl_hours else None,
        created_at=now, updated_at=now,
    )
    db.add(indicator)
    db.commit()
    db.refresh(indicator)
    return _serialize(indicator)


@router.get("/health")
async def ti_health(request: Request, db: Session = Depends(db_with_tenant)):
    tid = tenant_id(request)
    _seed_global_feed(db, tid)
    now = datetime.now(UTC)
    count = db.query(ThreatIntelIndicator).filter(
        ThreatIntelIndicator.tenant_id == tid,
        or_(ThreatIntelIndicator.expires_at.is_(None), ThreatIntelIndicator.expires_at > now),
    ).count()
    db.commit()
    return {"status": "ok" if count else "degraded", "feed": "database-backed", "active_indicators": count,
            "checked_at": now.isoformat()}
