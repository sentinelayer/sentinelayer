from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from control_plane.app.api.deps import db_with_tenant, tenant_id
from control_plane.app.infrastructure.db.models import Evidence, GateEvaluation, Requirement

router = APIRouter(prefix="/gates", tags=["gates"])


class RequirementCreate(BaseModel):
    requirement_id: str = Field(min_length=1, max_length=64)
    owner: str = Field(min_length=1, max_length=128)
    requirement: str = Field(min_length=1)
    acceptance_criteria: list[str] = Field(default_factory=list)
    security_impact: str = ""
    test_method: str = ""
    failure_behavior: str = ""
    rollback_strategy: str = ""
    dependency: list[str] = Field(default_factory=list)
    reviewer: str = "External Retainer"
    criticality: str = "P1"
    gate: str = "MVP"


class CheckUpdate(BaseModel):
    implementation_pass: bool | None = None
    automated_test_pass: bool | None = None
    security_test_pass: bool | None = None
    evidence_valid: bool | None = None
    independent_reviewer_valid: bool | None = None
    residual_risk_accepted: bool | None = None
    dependency_check_pass: bool | None = None
    rollback_test_pass: bool | None = None
    drift_detected: bool | None = None
    implementation_version: str | None = None


def _json_list(value: str | None) -> list[str]:
    try:
        parsed = json.loads(value or "[]")
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _serialize(row: Requirement) -> dict[str, Any]:
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "owner": row.owner,
        "requirement": row.requirement,
        "acceptance_criteria": _json_list(row.acceptance_criteria),
        "security_impact": row.security_impact,
        "test_method": row.test_method,
        "failure_behavior": row.failure_behavior,
        "rollback_strategy": row.rollback_strategy,
        "dependency": _json_list(row.dependency),
        "evidence_ids": _json_list(row.evidence_ids),
        "reviewer": row.reviewer,
        "criticality": row.criticality,
        "gate": row.gate,
        "status": row.status,
        "implementation_version": row.implementation_version,
        "checks": {
            "implementation_pass": row.implementation_pass,
            "automated_test_pass": row.automated_test_pass,
            "security_test_pass": row.security_test_pass,
            "evidence_valid": row.evidence_valid,
            "independent_reviewer_valid": row.independent_reviewer_valid,
            "residual_risk_accepted": row.residual_risk_accepted,
            "dependency_check_pass": row.dependency_check_pass,
            "rollback_test_pass": row.rollback_test_pass,
            "drift_detected": row.drift_detected,
        },
    }


def _checks(row: Requirement, db: Session, tid: str, visited: set[str]) -> tuple[list[dict[str, str]], bool]:
    dependency_ok = bool(row.dependency_check_pass)
    dependencies = _json_list(row.dependency)
    if dependencies:
        dependency_ok = True
        for dependency_id in dependencies:
            if dependency_id in visited:
                dependency_ok = False
                continue
            dependency = db.query(Requirement).filter(
                Requirement.id == dependency_id, Requirement.tenant_id == tid
            ).first()
            if not dependency:
                dependency_ok = False
                continue
            dependency_result = _evaluate(dependency, db, tid, None, visited)
            if dependency_result["status"] != "ACCEPTED":
                dependency_ok = False

    evidence_ok = bool(row.evidence_valid)
    evidence_ids = _json_list(row.evidence_ids)
    if evidence_ids:
        evidence_rows = db.query(Evidence).filter(
            Evidence.tenant_id == tid, Evidence.id.in_(evidence_ids)
        ).all()
        evidence_ok = len(evidence_rows) == len(evidence_ids) and all(e.status == "VALID" for e in evidence_rows)

    checks = [
        {"name": "Implementation", "status": "PASS" if row.implementation_pass else "FAIL"},
        {"name": "Automated Test", "status": "PASS" if row.automated_test_pass else "FAIL"},
        {"name": "Security Test", "status": "PASS" if row.security_test_pass else "FAIL"},
        {"name": "Evidence VALID", "status": "PASS" if evidence_ok else "FAIL"},
        {"name": "Independent Reviewer VALID", "status": "PASS" if row.independent_reviewer_valid else "FAIL"},
        {"name": "Residual Risk ACCEPTED", "status": "PASS" if row.residual_risk_accepted else "FAIL"},
        {"name": "Dependency Check", "status": "PASS" if dependency_ok else "FAIL"},
        {"name": "Rollback Test", "status": "PASS" if row.rollback_test_pass else "FAIL"},
        {"name": "No Configuration Drift", "status": "PASS" if not row.drift_detected else "FAIL"},
    ]
    return checks, all(item["status"] == "PASS" for item in checks)


def _evaluate(
    row: Requirement,
    db: Session,
    tid: str,
    evaluator: str | None,
    visited: set[str] | None = None,
) -> dict[str, Any]:
    visited = visited or set()
    if row.id in visited:
        return {"requirement_id": row.id, "status": row.status or "REJECTED", "all_pass": False}
    visited.add(row.id)
    checks, all_pass = _checks(row, db, tid, visited)
    status = "ACCEPTED" if all_pass else "REJECTED"
    now = datetime.now(UTC)
    payload = {"tenant_id": tid, "requirement_id": row.id, "checks": checks, "status": status,
               "implementation_version": row.implementation_version or ""}
    result_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    row.status = status
    row.updated_at = now
    db.add(GateEvaluation(
        id=str(uuid.uuid4()), tenant_id=tid, requirement_id=row.id, evaluator_id=evaluator,
        status=status, checks=json.dumps(checks, sort_keys=True), all_pass=all_pass,
        result_hash=result_hash, evaluated_at=now,
    ))
    return {
        "requirement_id": row.id, "status": status, "checks": checks, "all_pass": all_pass,
        "criticality": row.criticality, "gate": row.gate,
        "implementation_version": row.implementation_version or "", "evaluated_at": now.isoformat(),
        "hash": result_hash,
    }


@router.post("/requirements")
async def register_requirement(data: RequirementCreate, request: Request, db: Session = Depends(db_with_tenant)):
    tid = tenant_id(request)
    existing = db.query(Requirement).filter(Requirement.id == data.requirement_id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Requirement {data.requirement_id} already exists")
    now = datetime.now(UTC)
    row = Requirement(
        id=data.requirement_id, tenant_id=tid, owner=data.owner, requirement=data.requirement,
        acceptance_criteria=json.dumps(data.acceptance_criteria), security_impact=data.security_impact,
        test_method=data.test_method, failure_behavior=data.failure_behavior, rollback_strategy=data.rollback_strategy,
        dependency=json.dumps(data.dependency), reviewer=data.reviewer, criticality=data.criticality,
        gate=data.gate, status="NOT_STARTED", created_at=now, updated_at=now,
    )
    db.add(row)
    db.commit()
    return {"id": row.id, "tenant_id": tid, "status": row.status}


@router.get("/requirements")
async def list_requirements(request: Request, criticality: str | None = None, db: Session = Depends(db_with_tenant)):
    query = db.query(Requirement).filter(Requirement.tenant_id == tenant_id(request))
    if criticality:
        query = query.filter(Requirement.criticality == criticality)
    return [_serialize(row) for row in query.order_by(Requirement.created_at.asc()).all()]


@router.get("/requirements/{req_id}")
async def get_requirement(req_id: str, request: Request, db: Session = Depends(db_with_tenant)):
    row = db.query(Requirement).filter(Requirement.id == req_id, Requirement.tenant_id == tenant_id(request)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return _serialize(row)


@router.patch("/requirements/{req_id}/checks")
async def update_checks(req_id: str, data: CheckUpdate, request: Request, db: Session = Depends(db_with_tenant)):
    row = db.query(Requirement).filter(Requirement.id == req_id, Requirement.tenant_id == tenant_id(request)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Requirement not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    row.status = "NOT_STARTED"
    row.updated_at = datetime.now(UTC)
    db.commit()
    return {"id": row.id, "updated": True, "status": row.status}


@router.post("/requirements/{req_id}/evaluate")
async def evaluate_requirement(req_id: str, request: Request, db: Session = Depends(db_with_tenant)):
    tid = tenant_id(request)
    row = db.query(Requirement).filter(Requirement.id == req_id, Requirement.tenant_id == tid).first()
    if not row:
        raise HTTPException(status_code=404, detail="Requirement not found")
    result = _evaluate(row, db, tid, getattr(request.state, "user_id", None))
    db.commit()
    return result


@router.get("/production-ready")
async def production_ready(request: Request, db: Session = Depends(db_with_tenant)):
    tid = tenant_id(request)
    rows = db.query(Requirement).filter(
        Requirement.tenant_id == tid, Requirement.criticality.in_(["P0", "P1"])
    ).order_by(Requirement.created_at.asc()).all()
    if not rows:
        return {"ready": False, "reason": "No P0/P1 requirements registered", "p0_p1_total": 0,
                "p0_p1_accepted": 0, "coverage": 0.0, "coverage_threshold": 0.95}
    results = [_evaluate(row, db, tid, getattr(request.state, "user_id", None)) for row in rows]
    db.commit()
    accepted = sum(result["status"] == "ACCEPTED" for result in results)
    coverage = accepted / len(rows)
    return {
        "ready": accepted == len(rows) and coverage >= 0.95,
        "p0_p1_total": len(rows), "p0_p1_accepted": accepted,
        "coverage": round(coverage, 4), "coverage_threshold": 0.95,
        "evaluated_at": datetime.now(UTC).isoformat(),
    }
