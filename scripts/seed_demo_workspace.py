"""Seed a clearly labelled demo workspace for evaluation.

Usage:
  DEMO_TENANT_ID=demo-sentinellayer python -m scripts.seed_demo_workspace

The script is intentionally opt-in and refuses to run against a tenant id that
looks like a production tenant unless DEMO_SEED_ALLOW_NONDEMO=1 is supplied.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import UTC, datetime, timedelta

from control_plane.app.infrastructure.db.models import (
    Alert,
    Application,
    Evidence,
    Incident,
    Policy,
    PolicyVersion,
    RiskDecisionRecord,
    RuntimeEvent,
    Tenant,
)
from control_plane.app.infrastructure.db.session import SessionLocal, set_tenant_context

DEMO_TENANT_ID = os.getenv("DEMO_TENANT_ID", "demo-sentinellayer")


def stable_id(prefix: str, value: str) -> str:
    return f"{prefix}-{hashlib.sha256(value.encode()).hexdigest()[:20]}"


def run() -> None:
    if not DEMO_TENANT_ID.startswith("demo-") and os.getenv("DEMO_SEED_ALLOW_NONDEMO") != "1":
        raise SystemExit("Refusing to seed a non-demo tenant. Use a tenant id beginning with demo-.")

    db = SessionLocal()
    try:
        set_tenant_context(db, DEMO_TENANT_ID)
        tenant = db.get(Tenant, DEMO_TENANT_ID)
        if tenant is None:
            tenant = Tenant(id=DEMO_TENANT_ID, name="SentinelLayer Evaluation Workspace")
            db.add(tenant)

        applications = [
            ("customer-api", "Customer API", "production"),
            ("checkout-service", "Checkout Service", "production"),
            ("identity-gateway", "Identity Gateway", "staging"),
        ]
        app_rows: dict[str, Application] = {}
        for key, name, environment in applications:
            app_id = stable_id("app", key)
            row = db.get(Application, app_id)
            if row is None:
                row = Application(id=app_id, tenant_id=DEMO_TENANT_ID, name=name, environment=environment)
                db.add(row)
            app_rows[key] = row

        policy_id = stable_id("policy", "public-api-baseline")
        policy = db.get(Policy, policy_id)
        rules = {"mode": "monitor", "threshold": 70, "signals": ["waf", "behavior", "rate_limit"]}
        if policy is None:
            policy = Policy(id=policy_id, tenant_id=DEMO_TENANT_ID, application_id=app_rows["customer-api"].id, name="Public API Baseline", rules=json.dumps(rules), current_version=1)
            db.add(policy)
            db.add(PolicyVersion(id=stable_id("policy-version", policy_id), policy_id=policy_id, tenant_id=DEMO_TENANT_ID, version=1, rules=json.dumps(rules), signature="demo-fixture", signing_key_id="demo-fixture"))

        now = datetime.now(UTC)
        event_specs = [
            ("evt-safe-checkout", "request.decision", "Customer API", "low", 18, "ALLOW", {"endpoint": "/api/v1/orders", "application": "Checkout Service"}),
            ("evt-sqli-search", "waf.block", "Customer API", "high", 96, "BLOCK", {"endpoint": "/api/v1/search", "rule": "CRS SQLi", "application": "Customer API"}),
            ("evt-login-burst", "behavior.anomaly", "Identity Gateway", "medium", 78, "CHALLENGE", {"endpoint": "/api/v1/auth/login", "signal": "credential burst", "application": "Identity Gateway"}),
        ]
        for key, event_type, source, severity, score, outcome, data in event_specs:
            event_id = stable_id("event", key)
            event = db.get(RuntimeEvent, event_id)
            if event is None:
                event = RuntimeEvent(id=event_id, tenant_id=DEMO_TENANT_ID, event_type=event_type, source=source, severity=severity, risk_score=score, outcome=outcome, data=json.dumps(data), occurred_at=now - timedelta(minutes=len(key)))
                db.add(event)
                db.add(RiskDecisionRecord(id=stable_id("decision", key), tenant_id=DEMO_TENANT_ID, event_id=event_id, score=score, confidence=92, action=outcome, factors=json.dumps({"fixture": True, "reason": data.get("rule", data.get("signal", "baseline"))}), model_version="demo-rule-v1"))

        incident_id = stable_id("incident", "credential-burst")
        if db.get(Incident, incident_id) is None:
            db.add(Incident(id=incident_id, tenant_id=DEMO_TENANT_ID, severity="medium", status="investigating", description="Credential burst detected against Identity Gateway; challenge policy is active."))

        alert_id = stable_id("alert", "sqli-search")
        if db.get(Alert, alert_id) is None:
            db.add(Alert(id=alert_id, tenant_id=DEMO_TENANT_ID, severity="high", status="active", source="demo-fixture", message="SQL injection attempt blocked by OWASP CRS."))

        artifact = "demo-fixture://security-review/2026-08"
        evidence_id = stable_id("evidence", artifact)
        if db.get(Evidence, evidence_id) is None:
            digest = hashlib.sha256(artifact.encode()).hexdigest()
            db.add(Evidence(id=evidence_id, tenant_id=DEMO_TENANT_ID, requirement_id="DEMO-SEC-01", control_id="WAF-BASELINE", artifact=artifact, artifact_type="fixture", hash_sha256=digest, owner="SentinelLayer Demo", status="VALID", implementation_version="demo-2026.08", current_system_version="demo-2026.08", chain_of_custody=json.dumps([{"actor": "demo-seeder", "action": "created"}])))

        db.commit()
        print(f"Seeded idempotent demo workspace: {DEMO_TENANT_ID}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
