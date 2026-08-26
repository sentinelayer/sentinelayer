"""Customer offboarding lifecycle — Blueprint §9.19"""
import hashlib
import json
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from control_plane.app.api.deps import db_with_tenant, tenant_id
from control_plane.app.infrastructure.db.models import Application, Policy

router = APIRouter(prefix="/offboarding", tags=["offboarding"])


class OffboardRequest(BaseModel):
    confirm: bool = False
    mode: str = "soft"  # soft | hard


@router.post("/request")
async def request_offboard(data: OffboardRequest, request: Request, db: Session = Depends(db_with_tenant)):
    tid = tenant_id(request)
    if not data.confirm:
        raise HTTPException(status_code=400, detail="confirm=true required")
    apps = db.query(Application).filter(Application.tenant_id == tid).all()
    policies = db.query(Policy).filter(Policy.tenant_id == tid).all()
    before = {
        "apps": [a.id for a in apps],
        "policies": [p.id for p in policies],
        "at": datetime.now(UTC).isoformat(),
    }
    before_hash = hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest()

    if data.mode == "hard":
        for p in policies:
            db.delete(p)
        for a in apps:
            db.delete(a)
        db.commit()
        after = {"apps": [], "policies": [], "at": datetime.now(UTC).isoformat()}
    else:
        # soft: rename marker
        for a in apps:
            if not a.name.startswith("[OFFBOARD]"):
                a.name = f"[OFFBOARD] {a.name}"
        db.commit()
        after = {
            "apps": [a.id for a in apps],
            "policies": [p.id for p in policies],
            "at": datetime.now(UTC).isoformat(),
        }

    after_hash = hashlib.sha256(json.dumps(after, sort_keys=True).encode()).hexdigest()
    return {
        "tenant_id": tid,
        "mode": data.mode,
        "before_hash": before_hash,
        "after_hash": after_hash,
        "status": "completed",
    }
