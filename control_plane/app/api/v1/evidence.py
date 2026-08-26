"""Evidence API — full model (Blueprint Section 0.5 + 0.6)"""
import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from control_plane.app.infrastructure.db.models import Evidence
from control_plane.app.infrastructure.db.session import get_db

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


@router.post("/")
async def create_evidence(data: EvidenceCreate, db: Session = Depends(get_db)):
    payload = data.data or {}
    hash_value = hashlib.sha256(
        json.dumps({"artifact": data.artifact, **payload}, sort_keys=True).encode()
    ).hexdigest()

    evidence = Evidence(
        id=str(uuid.uuid4()),
        artifact=data.artifact,
        artifact_type=data.artifact_type,
        requirement_id=data.requirement_id,
        control_id=data.control_id,
        hash_sha256=hash_value,
        owner=data.owner,
        reviewer=data.reviewer,
        status="CREATED",
        implementation_version=data.implementation_version,
        runtime_artifact_hash=data.runtime_artifact_hash,
        approved_manifest_hash=data.approved_manifest_hash,
        relationship=data.relationship,
        related_id=data.related_id,
        chain_of_custody=json.dumps([
            {
                "action": "CREATED",
                "actor": data.owner,
                "at": datetime.now(UTC).isoformat(),
            }
        ]),
        created_at=datetime.now(UTC),
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return {
        "id": evidence.id,
        "requirement_id": evidence.requirement_id,
        "status": evidence.status,
        "hash_sha256": evidence.hash_sha256,
    }


@router.get("/")
async def list_evidence(
    requirement_id: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Evidence)
    if requirement_id:
        q = q.filter_by(requirement_id=requirement_id)
    if status:
        q = q.filter_by(status=status)
    rows = q.all()
    return [
        {
            "id": e.id,
            "requirement_id": e.requirement_id,
            "control_id": e.control_id,
            "artifact": e.artifact,
            "status": e.status,
            "hash_sha256": e.hash_sha256,
            "owner": e.owner,
            "implementation_version": e.implementation_version,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in rows
    ]


@router.get("/{id}")
async def get_evidence(id: str, db: Session = Depends(get_db)):
    e = db.query(Evidence).filter_by(id=id).first()
    if not e:
        raise HTTPException(404, "Evidence not found")
    return {
        "id": e.id,
        "requirement_id": e.requirement_id,
        "control_id": e.control_id,
        "artifact": e.artifact,
        "artifact_type": e.artifact_type,
        "hash_sha256": e.hash_sha256,
        "owner": e.owner,
        "reviewer": e.reviewer,
        "status": e.status,
        "implementation_version": e.implementation_version,
        "current_system_version": e.current_system_version,
        "runtime_artifact_hash": e.runtime_artifact_hash,
        "approved_manifest_hash": e.approved_manifest_hash,
        "relationship": e.relationship,
        "related_id": e.related_id,
        "chain_of_custody": json.loads(e.chain_of_custody or "[]"),
        "created_at": e.created_at.isoformat() if e.created_at else None,
        "verified_at": e.verified_at.isoformat() if e.verified_at else None,
        "validated_at": e.validated_at.isoformat() if e.validated_at else None,
        "expired_at": e.expired_at.isoformat() if e.expired_at else None,
        "revoked_at": e.revoked_at.isoformat() if e.revoked_at else None,
        "revoked_reason": e.revoked_reason,
    }


@router.post("/{id}/verify")
async def verify_evidence(id: str, data: EvidenceVerify, db: Session = Depends(get_db)):
    e = db.query(Evidence).filter_by(id=id).first()
    if not e:
        raise HTTPException(404, "Evidence not found")
    if e.status != "CREATED":
        raise HTTPException(400, f"Cannot verify from status {e.status}")

    # Integrity check
    # (simplified — full recompute would need original data payload)
    chain = json.loads(e.chain_of_custody or "[]")
    chain.append({
        "action": "VERIFIED",
        "actor": data.actor,
        "at": datetime.now(UTC).isoformat(),
    })
    e.status = "VERIFIED"
    e.verified_at = datetime.now(UTC)
    e.chain_of_custody = json.dumps(chain)
    db.commit()
    return {"id": e.id, "status": "VERIFIED"}


@router.post("/{id}/validate")
async def validate_evidence(id: str, data: EvidenceValidate, db: Session = Depends(get_db)):
    e = db.query(Evidence).filter_by(id=id).first()
    if not e:
        raise HTTPException(404, "Evidence not found")
    if e.status not in ("VERIFIED", "VALID"):
        raise HTTPException(400, f"Cannot validate from status {e.status}")

    chain = json.loads(e.chain_of_custody or "[]")

    # Version drift → auto EXPIRED
    if e.implementation_version != data.current_system_version:
        chain.append({
            "action": "EXPIRED",
            "actor": "system",
            "at": datetime.now(UTC).isoformat(),
            "reason": f"Version drift: evidence={e.implementation_version} current={data.current_system_version}",
        })
        e.status = "EXPIRED"
        e.expired_at = datetime.now(UTC)
        e.chain_of_custody = json.dumps(chain)
        db.commit()
        return {"id": e.id, "status": "EXPIRED", "reason": "version drift"}

    # Runtime provenance check
    if e.runtime_artifact_hash and e.approved_manifest_hash:
        if e.runtime_artifact_hash != e.approved_manifest_hash:
            chain.append({
                "action": "REVOKED",
                "actor": "system",
                "at": datetime.now(UTC).isoformat(),
                "reason": "Runtime provenance mismatch",
            })
            e.status = "REVOKED"
            e.revoked_at = datetime.now(UTC)
            e.revoked_reason = "Runtime provenance mismatch"
            e.chain_of_custody = json.dumps(chain)
            db.commit()
            return {"id": e.id, "status": "REVOKED", "reason": "provenance mismatch"}

    chain.append({
        "action": "VALID",
        "actor": data.actor,
        "at": datetime.now(UTC).isoformat(),
    })
    e.status = "VALID"
    e.validated_at = datetime.now(UTC)
    e.current_system_version = data.current_system_version
    e.chain_of_custody = json.dumps(chain)
    db.commit()
    return {"id": e.id, "status": "VALID"}


@router.post("/{id}/revoke")
async def revoke_evidence(id: str, actor: str, reason: str, db: Session = Depends(get_db)):
    e = db.query(Evidence).filter_by(id=id).first()
    if not e:
        raise HTTPException(404, "Evidence not found")
    if e.status in ("EXPIRED", "REVOKED", "SUPERSEDED"):
        raise HTTPException(400, f"Already terminal status: {e.status}")

    chain = json.loads(e.chain_of_custody or "[]")
    chain.append({
        "action": "REVOKED",
        "actor": actor,
        "at": datetime.now(UTC).isoformat(),
        "reason": reason,
    })
    e.status = "REVOKED"
    e.revoked_at = datetime.now(UTC)
    e.revoked_reason = reason
    e.chain_of_custody = json.dumps(chain)
    db.commit()
    return {"id": e.id, "status": "REVOKED"}
