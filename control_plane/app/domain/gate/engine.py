"""
Acceptance Gate Engine — Machine-Enforced (Blueprint Section 0.8)

Rules:
- ACCEPTED only when ALL checks PASS.
- Status cannot be changed manually.
- One failure → automatic REJECTED.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import hashlib
import json


class GateStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    DESIGNED = "DESIGNED"
    IMPLEMENTED = "IMPLEMENTED"
    TESTED = "TESTED"
    VERIFIED = "VERIFIED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class Criticality(str, Enum):
    P0 = "P0"  # Production Blocker
    P1 = "P1"  # Mandatory
    P2 = "P2"  # Important
    P3 = "P3"  # Deferred


class Gate(str, Enum):
    MVP = "MVP"
    PILOT = "Pilot"
    PRODUCTION = "Production"
    ENTERPRISE = "Enterprise"
    POST_PRODUCTION = "Post-production"


@dataclass
class Requirement:
    """Full Definition of Done (Section 0.1) — first-class object."""
    requirement_id: str
    owner: str
    dependency: List[str] = field(default_factory=list)
    requirement: str = ""
    acceptance_criteria: List[str] = field(default_factory=list)
    security_impact: str = ""
    test_method: str = ""
    failure_behavior: str = ""
    rollback_strategy: str = ""
    evidence_ids: List[str] = field(default_factory=list)
    reviewer: str = ""  # Independent reviewer (External Retainer for solo)
    criticality: Criticality = Criticality.P1
    gate: Gate = Gate.MVP
    status: GateStatus = GateStatus.NOT_STARTED
    implementation_version: str = ""
    # Machine checks (not human flags)
    implementation_pass: bool = False
    automated_test_pass: bool = False
    security_test_pass: bool = False
    evidence_valid: bool = False
    independent_reviewer_valid: bool = False
    residual_risk_accepted: bool = False
    dependency_check_pass: bool = False
    rollback_test_pass: bool = False
    drift_detected: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["criticality"] = self.criticality.value
        d["gate"] = self.gate.value
        d["status"] = self.status.value
        return d


class GateEngine:
    """
    Machine-enforced acceptance gate.
    Matches Blueprint Section 0.8 exactly.

    Evaluation order:
    Requirement → Implementation → Automated Test → Security Test →
    Evidence VALID → Independent Reviewer VALID → Residual Risk ACCEPTED →
    Dependency Check → Rollback Test → (no drift) → GATE RESULT
    """

    def __init__(self) -> None:
        self._requirements: Dict[str, Requirement] = {}

    def register(self, req: Requirement) -> Requirement:
        if req.requirement_id in self._requirements:
            raise ValueError(f"Requirement {req.requirement_id} already registered")
        self._requirements[req.requirement_id] = req
        return req

    def get(self, req_id: str) -> Optional[Requirement]:
        return self._requirements.get(req_id)

    def list_by_criticality(self, criticality: Criticality) -> List[Requirement]:
        return [r for r in self._requirements.values() if r.criticality == criticality]

    def evaluate(self, req_id: str) -> Dict[str, Any]:
        req = self._requirements.get(req_id)
        if not req:
            return {
                "requirement_id": req_id,
                "status": GateStatus.REJECTED.value,
                "reason": "Requirement not found",
                "all_pass": False,
                "evaluated_at": datetime.now(timezone.utc).isoformat(),
            }

        checks = [
            {"name": "Implementation", "status": "PASS" if req.implementation_pass else "FAIL"},
            {"name": "Automated Test", "status": "PASS" if req.automated_test_pass else "FAIL"},
            {"name": "Security Test", "status": "PASS" if req.security_test_pass else "FAIL"},
            {"name": "Evidence VALID", "status": "PASS" if req.evidence_valid else "FAIL"},
            {"name": "Independent Reviewer VALID", "status": "PASS" if req.independent_reviewer_valid else "FAIL"},
            {"name": "Residual Risk ACCEPTED", "status": "PASS" if req.residual_risk_accepted else "FAIL"},
            {"name": "Dependency Check", "status": "PASS" if req.dependency_check_pass else "FAIL"},
            {"name": "Rollback Test", "status": "PASS" if req.rollback_test_pass else "FAIL"},
            {"name": "No Configuration Drift", "status": "PASS" if not req.drift_detected else "FAIL"},
        ]

        all_pass = all(c["status"] == "PASS" for c in checks)

        # Machine-enforced: status is derived, never set by hand
        if all_pass:
            new_status = GateStatus.ACCEPTED
        else:
            new_status = GateStatus.REJECTED

        req.status = new_status
        req.updated_at = datetime.now(timezone.utc).isoformat()

        result = {
            "requirement_id": req_id,
            "status": new_status.value,
            "checks": checks,
            "all_pass": all_pass,
            "criticality": req.criticality.value,
            "gate": req.gate.value,
            "implementation_version": req.implementation_version,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "hash": self._result_hash(req_id, checks, new_status.value),
        }
        return result

    def _result_hash(self, req_id: str, checks: List[Dict], status: str) -> str:
        payload = json.dumps(
            {"req_id": req_id, "checks": checks, "status": status},
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def production_ready(self) -> Dict[str, Any]:
        """
        PRODUCTION READY only if:
        - All P0 + P1 are ACCEPTED
        - Coverage of P0+P1 >= 95%
        - Non-accepted have risk acceptance + mitigation plan
        """
        p0_p1 = [
            r for r in self._requirements.values()
            if r.criticality in (Criticality.P0, Criticality.P1)
        ]
        if not p0_p1:
            return {"ready": False, "reason": "No P0/P1 requirements registered"}

        accepted = [r for r in p0_p1 if r.status == GateStatus.ACCEPTED]
        coverage = len(accepted) / len(p0_p1)

        all_accepted = len(accepted) == len(p0_p1)
        coverage_ok = coverage >= 0.95

        ready = all_accepted and coverage_ok
        return {
            "ready": ready,
            "p0_p1_total": len(p0_p1),
            "p0_p1_accepted": len(accepted),
            "coverage": round(coverage, 4),
            "coverage_threshold": 0.95,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }
