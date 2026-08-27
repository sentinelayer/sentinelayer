"""Evidence API — integrity, lifecycle, provenance, and tenant isolation."""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from control_plane.app.api.deps import db_with_tenant, tenant_id
from control_plane.app.infrastructure.db.models import Evidence

router = APIRouter(prefix="/evidence", tags=["evidence"])


class EvidenceCreate(BaseModel):
    artifact: str
    requirement_id: str
    control_id: str
    owner: str
    implementation_version: str
    artifact_type: str = "file"
    reviewer: str | None = None
    relationship: str | None = None
    related_id: str | None = None
    runtime_artifact_hash: str | None = None
    approved_manifest_hash: str | None = None
    data: dict[str, Any] | None = None


class EvidenceVerify(BaseModel):
    actor: str


class EvidenceValidate(BaseModel):
    actor: str
    current_system_version: str



def _actor(request: Request, supplied: str | None = None) -> str:
    current = getattr(request.state, "user_id", None)
    if current and supplied and current != supplied:
        raise HTTPException(status_code=403, detail="Actor must match authenticated user")
    return current or supplied or "system"


def _get(id: str, tid: str, db: Session) -> Evidence:
    evidence = db.query(Evidence).filter(Evidence.id == id, Evidence.tenant_id == tid).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return evidence


def _chain(evidence: Evidence) -> list[dict[str, Any]]:
    try:
        value = json.loads(evidence.chain_of_custody or "[]")
    except json.JSONDecodeError:
        value = []
    return value if isinstance(value, list) else []


def _serialize(e: Evidence, include_artifact: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {
        "id": e.id, "tenant_id": e.tenant_id, "requirement_id": e.requirement_id,
        "control_id": e.control_id, "status": e.status, "hash_sha256": e.hash_sha256,
        "owner": e.owner, "implementation_version": e.implementation_version,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }
    if include_artifact:
        result.update({
            "artifact": e.artifact, "artifact_type": e.artifact_type, "reviewer": e.reviewer,
            "current_system_version": e.current_system_version,
            "runtime_artifact_hash": e.runtime_artifact_hash,
            "approved_manifest_hash": e.approved_manifest_hash,
            "relationship": e.relationship, "related_id": e.related_id,
            "chain_of_custody": _chain(e),
            "verified_at": e.verified_at.isoformat() if e.verified_at else None,
            "validated_at": e.validated_at.isoformat() if e.validated_at else None,
            "expired_at": e.expired_at.isoformat() if e.expired_at else None,
            "revoked_at": e.revoked_at.isoformat() if e.revoked_at else None,
            "revoked_reason": e.revoked_reason,
        })
    return result


@router.post("/")
@router.post("")
async def create_evidence(data: EvidenceCreate, request: Request, db: Session = Depends(db_with_tenant)):
    tid = tenant_id(request)
    payload = data.data or {}
    hash_value = hashlib.sha256(json.dumps({"artifact": data.artifact, **payload}, sort_keys=True).encode()).hexdigest()
    now = datetime.now(UTC)
    evidence = Evidence(
        id=str(uuid.uuid4()), tenant_id=tid, artifact=data.artifact, artifact_type=data.artifact_type,
        requirement_id=data.requirement_id, control_id=data.control_id, hash_sha256=hash_value,
        owner=data.owner, reviewer=data.reviewer, status="CREATED", implementation_version=data.implementation_version,
        runtime_artifact_hash=data.runtime_artifact_hash, approved_manifest_hash=data.approved_manifest_hash,
        relationship=data.relationship, related_id=data.related_id,
        chain_of_custody=json.dumps([{"action": "CREATED", "actor": _actor(request), "owner": data.owner, "at": now.isoformat()}]),
        created_at=now,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return _serialize(evidence)


@router.get("/")
@router.get("")
async def list_evidence(
    request: Request,
    requirement_id: str | None = None,
    status: str | None = None,
    db: Session = Depends(db_with_tenant),
):
    tid = tenant_id(request)
    query = db.query(Evidence).filter(Evidence.tenant_id == tid)
    if requirement_id:
        query = query.filter(Evidence.requirement_id == requirement_id)
    if status:
        query = query.filter(Evidence.status == status)
    return [_serialize(evidence) for evidence in query.order_by(Evidence.created_at.desc()).all()]


@router.get("/{id}")
async def get_evidence(id: str, request: Request, db: Session = Depends(db_with_tenant)):
    return _serialize(_get(id, tenant_id(request), db), include_artifact=True)


@router.post("/{id}/verify")
async def verify_evidence(id: str, data: EvidenceVerify, request: Request, db: Session = Depends(db_with_tenant)):
    evidence = _get(id, tenant_id(request), db)
    actor = _actor(request, data.actor)
    if evidence.status != "CREATED":
        raise HTTPException(400, f"Cannot verify from status {evidence.status}")
    chain = _chain(evidence)
    chain.append({"action": "VERIFIED", "actor": actor, "at": datetime.now(UTC).isoformat()})
    evidence.status = "VERIFIED"
    evidence.verified_at = datetime.now(UTC)
    evidence.chain_of_custody = json.dumps(chain)
    db.commit()
    return {"id": evidence.id, "status": "VERIFIED"}


@router.post("/{id}/validate")
async def validate_evidence(id: str, data: EvidenceValidate, request: Request, db: Session = Depends(db_with_tenant)):
    evidence = _get(id, tenant_id(request), db)
    actor = _actor(request, data.actor)
    if evidence.status not in ("VERIFIED", "VALID"):
        raise HTTPException(400, f"Cannot validate from status {evidence.status}")
    chain = _chain(evidence)
    now = datetime.now(UTC)
    if evidence.implementation_version != data.current_system_version:
        chain.append({"action": "EXPIRED", "actor": actor, "at": now.isoformat(),
                      "reason": f"Version drift: evidence={evidence.implementation_version} current={data.current_system_version}"})
        evidence.status = "EXPIRED"
        evidence.expired_at = now
        evidence.chain_of_custody = json.dumps(chain)
        db.commit()
        return {"id": evidence.id, "status": "EXPIRED", "reason": "version drift"}
    if evidence.runtime_artifact_hash and evidence.approved_manifest_hash:
        if evidence.runtime_artifact_hash != evidence.approved_manifest_hash:
            chain.append({"action": "REVOKED", "actor": actor, "at": now.isoformat(), "reason": "Runtime provenance mismatch"})
            evidence.status = "REVOKED"
            evidence.revoked_at = now
            evidence.revoked_reason = "Runtime provenance mismatch"
            evidence.chain_of_custody = json.dumps(chain)
            db.commit()
            return {"id": evidence.id, "status": "REVOKED", "reason": "provenance mismatch"}
    chain.append({"action": "VALID", "actor": actor, "at": now.isoformat()})
    evidence.status = "VALID"
    evidence.validated_at = now
    evidence.current_system_version = data.current_system_version
    evidence.chain_of_custody = json.dumps(chain)
    db.commit()
    return {"id": evidence.id, "status": "VALID"}


@router.post("/{id}/revoke")
async def revoke_evidence(
    id: str,
    request: Request,
    reason: str = Query(min_length=1, max_length=2000),
    db: Session = Depends(db_with_tenant),
):
    evidence = _get(id, tenant_id(request), db)
    actor = _actor(request)
    if evidence.status in ("EXPIRED", "REVOKED", "SUPERSEDED"):
        raise HTTPException(400, f"Already terminal status: {evidence.status}")
    now = datetime.now(UTC)
    chain = _chain(evidence)
    chain.append({"action": "REVOKED", "actor": actor, "at": now.isoformat(), "reason": reason})
    evidence.status = "REVOKED"
    evidence.revoked_at = now
    evidence.revoked_reason = reason
    evidence.chain_of_custody = json.dumps(chain)
    db.commit()
    return {"id": evidence.id, "status": "REVOKED"}
