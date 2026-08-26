"""Gate Engine API — machine-enforced acceptance (Section 0.8)"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import json
from datetime import datetime, timezone

from control_plane.app.infrastructure.db.session import get_db
from control_plane.app.infrastructure.db.models import Requirement
from control_plane.app.domain.gate.engine import (
    GateEngine, Requirement as ReqDomain,
    Criticality, Gate, GateStatus
)

router = APIRouter(prefix="/gates", tags=["gates"])

# In-memory engine instance (will be replaced by DB-backed later)
_engine = GateEngine()


class RequirementCreate(BaseModel):
    requirement_id: str
    owner: str
    requirement: str
    acceptance_criteria: List[str] = []
    security_impact: str = ""
    test_method: str = ""
    failure_behavior: str = ""
    rollback_strategy: str = ""
    dependency: List[str] = []
    reviewer: str = "External Retainer"
    criticality: str = "P1"
    gate: str = "MVP"


class CheckUpdate(BaseModel):
    implementation_pass: Optional[bool] = None
    automated_test_pass: Optional[bool] = None
    security_test_pass: Optional[bool] = None
    evidence_valid: Optional[bool] = None
    independent_reviewer_valid: Optional[bool] = None
    residual_risk_accepted: Optional[bool] = None
    dependency_check_pass: Optional[bool] = None
    rollback_test_pass: Optional[bool] = None
    drift_detected: Optional[bool] = None
    implementation_version: Optional[str] = None


@router.post("/requirements")
async def register_requirement(data: RequirementCreate, db: Session = Depends(get_db)):
    existing = db.query(Requirement).filter_by(id=data.requirement_id).first()
    if existing:
        raise HTTPException(400, f"Requirement {data.requirement_id} already exists")

    row = Requirement(
        id=data.requirement_id,
        owner=data.owner,
        requirement=data.requirement,
        acceptance_criteria=json.dumps(data.acceptance_criteria),
        security_impact=data.security_impact,
        test_method=data.test_method,
        failure_behavior=data.failure_behavior,
        rollback_strategy=data.rollback_strategy,
        dependency=json.dumps(data.dependency),
        reviewer=data.reviewer,
        criticality=data.criticality,
        gate=data.gate,
        status="NOT_STARTED",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(row)
    db.commit()

    # Also register in engine
    domain_req = ReqDomain(
        requirement_id=data.requirement_id,
        owner=data.owner,
        requirement=data.requirement,
        acceptance_criteria=data.acceptance_criteria,
        security_impact=data.security_impact,
        test_method=data.test_method,
        failure_behavior=data.failure_behavior,
        rollback_strategy=data.rollback_strategy,
        dependency=data.dependency,
        reviewer=data.reviewer,
        criticality=Criticality(data.criticality),
        gate=Gate(data.gate),
    )
    try:
        _engine.register(domain_req)
    except ValueError:
        pass  # already in engine

    return {"id": data.requirement_id, "status": "NOT_STARTED"}


@router.get("/requirements")
async def list_requirements(criticality: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Requirement)
    if criticality:
        q = q.filter_by(criticality=criticality)
    rows = q.all()
    return [
        {
            "id": r.id,
            "owner": r.owner,
            "requirement": r.requirement,
            "criticality": r.criticality,
            "gate": r.gate,
            "status": r.status,
            "implementation_pass": r.implementation_pass,
            "automated_test_pass": r.automated_test_pass,
            "security_test_pass": r.security_test_pass,
            "evidence_valid": r.evidence_valid,
            "independent_reviewer_valid": r.independent_reviewer_valid,
        }
        for r in rows
    ]


@router.get("/requirements/{req_id}")
async def get_requirement(req_id: str, db: Session = Depends(get_db)):
    r = db.query(Requirement).filter_by(id=req_id).first()
    if not r:
        raise HTTPException(404, "Requirement not found")
    return {
        "id": r.id,
        "owner": r.owner,
        "requirement": r.requirement,
        "acceptance_criteria": json.loads(r.acceptance_criteria or "[]"),
        "security_impact": r.security_impact,
        "test_method": r.test_method,
        "failure_behavior": r.failure_behavior,
        "rollback_strategy": r.rollback_strategy,
        "dependency": json.loads(r.dependency or "[]"),
        "reviewer": r.reviewer,
        "criticality": r.criticality,
        "gate": r.gate,
        "status": r.status,
        "implementation_version": r.implementation_version,
        "checks": {
            "implementation_pass": r.implementation_pass,
            "automated_test_pass": r.automated_test_pass,
            "security_test_pass": r.security_test_pass,
            "evidence_valid": r.evidence_valid,
            "independent_reviewer_valid": r.independent_reviewer_valid,
            "residual_risk_accepted": r.residual_risk_accepted,
            "dependency_check_pass": r.dependency_check_pass,
            "rollback_test_pass": r.rollback_test_pass,
            "drift_detected": r.drift_detected,
        },
    }


@router.patch("/requirements/{req_id}/checks")
async def update_checks(req_id: str, data: CheckUpdate, db: Session = Depends(get_db)):
    r = db.query(Requirement).filter_by(id=req_id).first()
    if not r:
        raise HTTPException(404, "Requirement not found")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(r, field, value)
    r.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"id": req_id, "updated": True}


@router.post("/requirements/{req_id}/evaluate")
async def evaluate_requirement(req_id: str, db: Session = Depends(get_db)):
    r = db.query(Requirement).filter_by(id=req_id).first()
    if not r:
        raise HTTPException(404, "Requirement not found")

    # Sync to engine
    domain_req = ReqDomain(
        requirement_id=r.id,
        owner=r.owner,
        requirement=r.requirement,
        criticality=Criticality(r.criticality),
        gate=Gate(r.gate),
        status=GateStatus(r.status) if r.status in [s.value for s in GateStatus] else GateStatus.NOT_STARTED,
        implementation_pass=r.implementation_pass,
        automated_test_pass=r.automated_test_pass,
        security_test_pass=r.security_test_pass,
        evidence_valid=r.evidence_valid,
        independent_reviewer_valid=r.independent_reviewer_valid,
        residual_risk_accepted=r.residual_risk_accepted,
        dependency_check_pass=r.dependency_check_pass,
        rollback_test_pass=r.rollback_test_pass,
        drift_detected=r.drift_detected,
        implementation_version=r.implementation_version or "",
    )
    if _engine.get(req_id) is None:
        _engine.register(domain_req)
    else:
        # update existing
        existing = _engine.get(req_id)
        for attr in [
            "implementation_pass", "automated_test_pass", "security_test_pass",
            "evidence_valid", "independent_reviewer_valid", "residual_risk_accepted",
            "dependency_check_pass", "rollback_test_pass", "drift_detected",
            "implementation_version",
        ]:
            setattr(existing, attr, getattr(r, attr))

    result = _engine.evaluate(req_id)

    # Persist status
    r.status = result["status"]
    r.updated_at = datetime.now(timezone.utc)
    db.commit()

    return result


@router.get("/production-ready")
async def production_ready(db: Session = Depends(get_db)):
    # Load all P0+P1 into engine
    rows = db.query(Requirement).filter(Requirement.criticality.in_(["P0", "P1"])).all()
    for r in rows:
        if _engine.get(r.id) is None:
            domain_req = ReqDomain(
                requirement_id=r.id,
                owner=r.owner,
                requirement=r.requirement,
                criticality=Criticality(r.criticality),
                gate=Gate(r.gate),
                status=GateStatus(r.status) if r.status in [s.value for s in GateStatus] else GateStatus.NOT_STARTED,
                implementation_pass=r.implementation_pass,
                automated_test_pass=r.automated_test_pass,
                security_test_pass=r.security_test_pass,
                evidence_valid=r.evidence_valid,
                independent_reviewer_valid=r.independent_reviewer_valid,
                residual_risk_accepted=r.residual_risk_accepted,
                dependency_check_pass=r.dependency_check_pass,
                rollback_test_pass=r.rollback_test_pass,
                drift_detected=r.drift_detected,
            )
            _engine.register(domain_req)

    return _engine.production_ready()
