"""Lightweight threat-intel feed (offline-capable)."""
from datetime import UTC, datetime

from fastapi import APIRouter, Header, HTTPException

router = APIRouter(prefix="/threat-intel", tags=["threat-intel"])

# Static curated indicators (replace with external feed later)
_FEED = [
    {"id": "ti-001", "type": "ip", "value": "203.0.113.50", "severity": "high", "source": "internal", "tags": ["scanner"]},
    {"id": "ti-002", "type": "ip", "value": "198.51.100.23", "severity": "medium", "source": "internal", "tags": ["bruteforce"]},
    {"id": "ti-003", "type": "ua", "value": "sqlmap", "severity": "high", "source": "internal", "tags": ["sqli-tool"]},
    {"id": "ti-004", "type": "path", "value": "/.env", "severity": "medium", "source": "internal", "tags": ["secret-scan"]},
]


@router.get("/indicators")
async def list_indicators(x_tenant_id: str | None = Header(None)):
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="Missing tenant ID")
    return {
        "count": len(_FEED),
        "updated_at": datetime.now(UTC).isoformat(),
        "indicators": _FEED,
    }


@router.get("/health")
async def ti_health():
    return {"status": "ok", "feed": "static-v1"}
