"""
Seed all P0 requirements into GateEngine / DB.
Run once after migration 0002.

Usage (from control_plane root):
    python -m app.domain.gate.seed_p0
"""
from __future__ import annotations

import json
from datetime import UTC, datetime

from control_plane.app.infrastructure.db.models import Requirement
from control_plane.app.infrastructure.db.session import SessionLocal

P0_REQUIREMENTS = [
    {
        "id": "SL-SEC-AUTH-001",
        "owner": "Founder",
        "requirement": "All protected API endpoints require valid JWT or API key",
        "acceptance_criteria": [
            "Unauthenticated request → 401",
            "Malformed JWT → 401",
            "Expired JWT → 401",
            "Valid JWT → request proceeds",
        ],
        "security_impact": "Unauthorized access to tenant data and control plane",
        "test_method": "Automated integration tests + adversarial matrix",
        "failure_behavior": "Fail-closed (reject request)",
        "rollback_strategy": "Revert auth middleware to previous signed version within 15 min",
        "dependency": [],
        "reviewer": "External Retainer",
        "criticality": "P0",
        "gate": "MVP",
    },
    {
        "id": "SL-SEC-AUTHZ-001",
        "owner": "Founder",
        "requirement": "Object-level authorization enforced (no BOLA/IDOR)",
        "acceptance_criteria": [
            "User A cannot read/write object belonging to User B",
            "Cross-tenant object access returns 403 or 404",
        ],
        "security_impact": "Cross-tenant data breach",
        "test_method": "Adversarial matrix tests for every object endpoint",
        "failure_behavior": "Fail-closed",
        "rollback_strategy": "Disable affected endpoint via feature flag",
        "dependency": ["SL-SEC-AUTH-001"],
        "reviewer": "External Retainer",
        "criticality": "P0",
        "gate": "MVP",
    },
    {
        "id": "SL-SEC-TENANT-001",
        "owner": "Founder",
        "requirement": "Tenant isolation adversarial matrix passes on all data paths",
        "acceptance_criteria": [
            "No cross-tenant read via direct ID",
            "No cross-tenant read via search/filter",
            "RLS policies active on all tenant-scoped tables",
        ],
        "security_impact": "Full tenant data exposure",
        "test_method": "Automated tenant isolation suite + manual adversarial review",
        "failure_behavior": "Fail-closed",
        "rollback_strategy": "Block affected tenant routes",
        "dependency": ["SL-SEC-AUTH-001", "SL-SEC-AUTHZ-001"],
        "reviewer": "External Retainer",
        "criticality": "P0",
        "gate": "MVP",
    },
    {
        "id": "SL-SEC-SECRET-001",
        "owner": "Founder",
        "requirement": "Secrets never appear in plaintext logs, error messages, or AI context",
        "acceptance_criteria": [
            "Log redaction active for known secret patterns",
            "Error responses never contain secrets",
            "AI/LLM prompts exclude secrets",
        ],
        "security_impact": "Credential leakage",
        "test_method": "Log scanning + prompt inspection tests",
        "failure_behavior": "Alert + continue (MONITOR)",
        "rollback_strategy": "Rotate leaked secrets immediately",
        "dependency": [],
        "reviewer": "External Retainer",
        "criticality": "P0",
        "gate": "MVP",
    },
    {
        "id": "SL-SEC-ENC-001",
        "owner": "Founder",
        "requirement": "TLS 1.3 in transit + AES-256 at rest for all sensitive data",
        "acceptance_criteria": [
            "All external endpoints serve TLS 1.3 only",
            "Database columns with PII/secrets encrypted at rest",
        ],
        "security_impact": "Data interception / offline compromise",
        "test_method": "TLS scan + encryption config verification",
        "failure_behavior": "Fail-closed for new connections",
        "rollback_strategy": "N/A (infra level)",
        "dependency": [],
        "reviewer": "External Retainer",
        "criticality": "P0",
        "gate": "MVP",
    },
    {
        "id": "SL-SEC-WAF-001",
        "owner": "Founder",
        "requirement": "Coraza WAF + OWASP CRS active on data plane",
        "acceptance_criteria": [
            "CRS ruleset loaded and enabled",
            "Known OWASP attack payloads blocked or logged per policy",
        ],
        "security_impact": "Unfiltered injection / XSS / RCE attempts reach app",
        "test_method": "DAST (ZAP) + CRS test suite",
        "failure_behavior": "Fail-closed for Critical; MONITOR for others",
        "rollback_strategy": "Revert WAF config to previous signed version",
        "dependency": [],
        "reviewer": "External Retainer",
        "criticality": "P0",
        "gate": "MVP",
    },
    {
        "id": "SL-SEC-SSRF-001",
        "owner": "Founder",
        "requirement": "SSRF protection: block private IP, cloud metadata, DNS rebinding",
        "acceptance_criteria": [
            "Requests to 169.254.169.254 blocked",
            "Private IP ranges blocked",
            "DNS rebinding mitigations active",
        ],
        "security_impact": "Internal network / cloud metadata compromise",
        "test_method": "SSRF payload suite",
        "failure_behavior": "Fail-closed",
        "rollback_strategy": "Block outbound from affected component",
        "dependency": [],
        "reviewer": "External Retainer",
        "criticality": "P0",
        "gate": "MVP",
    },
    {
        "id": "SL-SEC-SMUGGLING-001",
        "owner": "Founder",
        "requirement": "HTTP desync / request smuggling defenses active",
        "acceptance_criteria": [
            "CL.TE / TE.CL smuggling attempts rejected",
            "Normalized request parsing before upstream",
        ],
        "security_impact": "Bypass of WAF / auth / routing",
        "test_method": "HTTP smuggling test suite",
        "failure_behavior": "Fail-closed",
        "rollback_strategy": "Disable affected proxy path",
        "dependency": ["SL-SEC-WAF-001"],
        "reviewer": "External Retainer",
        "criticality": "P0",
        "gate": "MVP",
    },
    {
        "id": "SL-SEC-PROV-001",
        "owner": "Founder",
        "requirement": "Runtime provenance verification at startup",
        "acceptance_criteria": [
            "Binary / image hash matches approved manifest",
            "Mismatch → refuse to start",
        ],
        "security_impact": "Running tampered or unapproved code",
        "test_method": "Startup with mismatched hash must fail",
        "failure_behavior": "Fail-closed (do not start)",
        "rollback_strategy": "Deploy last known good signed artifact",
        "dependency": [],
        "reviewer": "External Retainer",
        "criticality": "P0",
        "gate": "MVP",
    },
    {
        "id": "SL-SEC-POLICY-001",
        "owner": "Founder",
        "requirement": "Policy signing key hierarchy + automatic 24h rotation",
        "acceptance_criteria": [
            "Policies signed before activation",
            "Signing key rotates every 24h",
            "Old key retained for verification window",
        ],
        "security_impact": "Unsigned / tampered policy activation",
        "test_method": "Key rotation integration test + signature verification",
        "failure_behavior": "Reject unsigned policy",
        "rollback_strategy": "Use previous key version within retention window",
        "dependency": [],
        "reviewer": "External Retainer",
        "criticality": "P0",
        "gate": "MVP",
    },
    {
        "id": "SL-SEC-FAIL-001",
        "owner": "Founder",
        "requirement": "Fail-open / fail-closed decision matrix enforced in Decision Safety Layer",
        "acceptance_criteria": [
            "Critical paths fail-closed on engine error",
            "Non-critical paths follow documented matrix",
            "Matrix itself is versioned and signed",
        ],
        "security_impact": "Unsafe default behavior under failure",
        "test_method": "Chaos / fault injection tests",
        "failure_behavior": "As defined by matrix",
        "rollback_strategy": "Revert Decision Safety config",
        "dependency": [],
        "reviewer": "External Retainer",
        "criticality": "P0",
        "gate": "MVP",
    },
    {
        "id": "SL-SEC-RL-001",
        "owner": "Founder",
        "requirement": "Abuse-economics rate limiting (multi-dimension)",
        "acceptance_criteria": [
            "Rate limits by IP, user, API key, tenant",
            "Cost-based throttling for expensive operations",
        ],
        "security_impact": "Resource exhaustion / abuse",
        "test_method": "Load test + limit verification",
        "failure_behavior": "Fail-closed (429)",
        "rollback_strategy": "Raise limits via signed config",
        "dependency": [],
        "reviewer": "External Retainer",
        "criticality": "P0",
        "gate": "MVP",
    },
]


def seed():
    db = SessionLocal()
    try:
        for item in P0_REQUIREMENTS:
            existing = db.query(Requirement).filter_by(id=item["id"]).first()
            if existing:
                print(f"SKIP {item['id']} (already exists)")
                continue

            row = Requirement(
                id=item["id"],
                owner=item["owner"],
                requirement=item["requirement"],
                acceptance_criteria=json.dumps(item["acceptance_criteria"]),
                security_impact=item["security_impact"],
                test_method=item["test_method"],
                failure_behavior=item["failure_behavior"],
                rollback_strategy=item["rollback_strategy"],
                dependency=json.dumps(item["dependency"]),
                reviewer=item["reviewer"],
                criticality=item["criticality"],
                gate=item["gate"],
                status="NOT_STARTED",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            db.add(row)
            print(f"SEED {item['id']}")
        db.commit()
        print("Done. 12 P0 requirements seeded.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
