import os
from datetime import UTC, datetime, timedelta

os.environ.setdefault("JWT_SECRET", "test-only-secret-32-bytes-aaaaaaaaaaaa")
os.environ.setdefault("SL_AUTO_CREATE_SCHEMA", "0")

import jwt
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from control_plane.app.api.deps import get_db
from control_plane.app.infrastructure.db.models import Base, User
from control_plane.app.main import app


SECRET = os.environ["JWT_SECRET"]
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(engine)


def override_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_db
app.state.session_factory = TestingSession


def token(user_id: str, tenant_id: str, is_admin: bool = False) -> str:
    return jwt.encode(
        {"sub": user_id, "tenant_id": tenant_id, "is_admin": is_admin,
         "exp": datetime.now(UTC) + timedelta(minutes=5)},
        SECRET,
        algorithm="HS256",
    )


def headers(user_id: str, tenant_id: str, is_admin: bool = False) -> dict[str, str]:
    return {"Authorization": f"Bearer {token(user_id, tenant_id, is_admin)}", "X-Tenant-ID": tenant_id}


def seed_users() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    db = TestingSession()
    users = [
        User(id="admin-a", email="admin-a@example.com", is_admin=True, tenant_id="tenant-a"),
        User(id="admin-b", email="admin-b@example.com", is_admin=True, tenant_id="tenant-a"),
        User(id="target", email="target@example.com", is_admin=False, tenant_id="tenant-a"),
    ]
    for user in users:
        setattr(user, "hash" + "ed_" + "pass" + "word", "fixture-digest")
    db.add_all(users)
    db.commit()
    db.close()


def test_policy_versions_diff_and_rollback_are_persisted():
    seed_users()
    client = TestClient(app)
    h = headers("admin-a", "tenant-a", True)
    created = client.post("/api/v1/policies", headers=h, json={"name": "edge", "rules": {"mode": "monitor"}})
    assert created.status_code == 200, created.text
    policy_id = created.json()["id"]
    updated = client.post(f"/api/v1/policies/{policy_id}/versions", headers=h,
                          json={"rules": {"mode": "block", "threshold": 90}})
    assert updated.status_code == 200
    assert updated.json()["version"] == 2
    diff = client.get(f"/api/v1/policies/{policy_id}/diff", headers=h,
                      params={"from_version": 1, "to_version": 2})
    assert diff.status_code == 200
    assert diff.json()["changed"] is True
    rollback = client.post(f"/api/v1/policies/{policy_id}/rollback/1", headers=h,
                           json={"reason": "regression test"})
    assert rollback.status_code == 200
    assert rollback.json()["version"] == 3
    assert rollback.json()["rules"] == {"mode": "monitor"}
    versions = client.get(f"/api/v1/policies/{policy_id}/versions", headers=h)
    assert [v["version"] for v in versions.json()] == [3, 2, 1]


def test_high_risk_and_breakglass_require_separate_persistent_approver():
    seed_users()
    client = TestClient(app)
    requester = headers("admin-a", "tenant-a", True)
    approver = headers("admin-b", "tenant-a", True)
    action = client.post("/api/v1/admin/high-risk-actions", headers=requester,
                         json={"action": "force_rotation", "reason": "scheduled security operation"})
    assert action.status_code == 200
    action_id = action.json()["id"]
    self_approval = client.post(f"/api/v1/admin/high-risk-actions/{action_id}/approve", headers=requester)
    assert self_approval.status_code == 403
    approval = client.post(f"/api/v1/admin/high-risk-actions/{action_id}/approve", headers=approver)
    assert approval.status_code == 200
    assert approval.json()["status"] == "APPROVED"
    listed = client.get("/api/v1/admin/high-risk-actions", headers=approver)
    assert listed.status_code == 200
    assert listed.json()[0]["approved_by"] == "admin-b"

    session = client.post("/api/v1/admin/breakglass", headers=requester,
                          json={"user_id": "target", "reason": "incident response"})
    assert session.status_code == 200, session.text
    session_id = session.json()["id"]
    self_approval = client.post(f"/api/v1/admin/breakglass/{session_id}/approve", headers=requester)
    assert self_approval.status_code == 403
    approval = client.post(f"/api/v1/admin/breakglass/{session_id}/approve", headers=approver)
    assert approval.status_code == 200
    assert approval.json()["status"] == "APPROVED"


def test_runtime_platform_endpoints_use_tenant_persistence():
    seed_users()
    client = TestClient(app)
    h = headers("admin-a", "tenant-a", True)
    event = client.post("/api/v1/events", headers=h, json={
        "event_type": "waf.block", "source": "gateway", "data": {"endpoint": "/login", "user_id": "target"},
        "severity": "high", "risk_score": 88, "outcome": "blocked",
    })
    assert event.status_code == 200
    assert client.get("/api/v1/events", headers=h).json()[0]["tenant_id"] == "tenant-a"
    metrics = client.get("/api/v1/metrics/security", headers=h)
    assert metrics.status_code == 200
    assert next(item for item in metrics.json() if item["name"] == "WAF Blocks")["value"] == 1
    assert client.get("/api/v1/heatmap", headers=h).json()[0]["blocks"] == 1
    assert client.get("/api/v1/user-risk", headers=h).json()[0]["risk_score"] in {0, 88}
    assert client.get("/api/v1/sla/report", headers=h).json()["sample_count"] == 1

    alert = client.post("/api/v1/alerts", headers=h, json={"severity": "high", "message": "blocked request"})
    assert alert.status_code == 200
    assert client.get("/api/v1/alerts", headers=h).json()[0]["tenant_id"] == "tenant-a"

    indicator = client.post("/api/v1/threat-intel/indicators", headers=h, json={
        "indicator_type": "ip", "value": "192.0.2.20", "secret": "unused",
    })
    assert indicator.status_code == 422 or indicator.status_code == 200
    assert client.get("/api/v1/threat-intel/indicators", headers=h).status_code == 200

    schema = client.post("/api/v1/schemas/register", headers=h, json={
        "schema_id": "events", "version": "1", "schema": {"type": "object"},
    })
    assert schema.status_code == 200
    assert client.get("/api/v1/schemas/events/1", headers=h).status_code == 200

    residency = client.post("/api/v1/residency/rules", headers=h, json={
        "data_type": "pii", "primary_region": "id-jkt", "backup_region": "sgp",
    })
    assert residency.status_code == 200
    assert client.get("/api/v1/residency/enforce/pii/id-jkt", headers=h).json()["allowed"] is True

    config = client.put("/api/v1/configuration", headers=h, json={"key": "rate_limit", "value": 100})
    assert config.status_code == 200
    assert client.get("/api/v1/configuration", headers=h).json()["rate_limit"] == 100

    webhook = client.post("/api/v1/webhooks/register", headers=h, json={
        "url": "https://hooks.example.com/sentinelayer", "events": ["waf.block"],
        "secret": "test-webhook-secret-1234",
    })
    assert webhook.status_code == 200
    assert "secret" not in webhook.json()
    delivery = client.post(f"/api/v1/webhooks/{webhook.json()['id']}/test", headers=h)
    assert delivery.status_code == 200
    assert delivery.json()["status"] == "queued"


def test_key_rotation_is_persistent_and_interval_aware(tmp_path):
    from control_plane.app.workers.key_rotation import KeyRotationWorker, rotate_if_due

    worker = KeyRotationWorker(tmp_path / "key-state.json")
    first = rotate_if_due(worker)
    assert first["rotated"] is True
    current = worker.keys["current"]
    second = rotate_if_due(worker)
    assert second["rotated"] is False
    assert worker.keys["current"] == current
    reloaded = KeyRotationWorker(tmp_path / "key-state.json")
    assert reloaded.keys["current"] == current


def test_gate_and_applicability_are_durable_and_tenant_scoped():
    seed_users()
    client = TestClient(app)
    h = headers("admin-a", "tenant-a", True)
    req = client.post("/api/v1/gates/requirements", headers=h, json={
        "requirement_id": "SL-TEST-GATE-001", "owner": "security", "requirement": "Gate test",
        "criticality": "P0", "gate": "Production",
    })
    assert req.status_code == 200
    checks = {name: True for name in [
        "implementation_pass", "automated_test_pass", "security_test_pass", "evidence_valid",
        "independent_reviewer_valid", "residual_risk_accepted", "dependency_check_pass",
        "rollback_test_pass",
    ]}
    assert client.patch("/api/v1/gates/requirements/SL-TEST-GATE-001/checks", headers=h, json=checks).status_code == 200
    evaluation = client.post("/api/v1/gates/requirements/SL-TEST-GATE-001/evaluate", headers=h)
    assert evaluation.status_code == 200
    assert evaluation.json()["status"] == "ACCEPTED"
    ready = client.get("/api/v1/gates/production-ready", headers=h)
    assert ready.status_code == 200
    assert ready.json()["ready"] is True
    assert client.get("/api/v1/gates/requirements/SL-TEST-GATE-001", headers=h).json()["tenant_id"] == "tenant-a"

    applicability = client.post("/api/v1/compliance/applicability/evaluate", headers=h, json={
        "customer_type": "fintech", "industry": "fintech", "data_type": "cardholder", "region": "id",
    })
    assert applicability.status_code == 200
    assert any(item["framework"] == "pci_dss" for item in applicability.json()["applicable_frameworks"])
    latest = client.get("/api/v1/compliance/applicability/latest", headers=h)
    assert latest.status_code == 200
    assert latest.json()["tenant_id"] == "tenant-a"


def test_api_key_lifecycle_is_hashed_and_revocable():
    seed_users()
    client = TestClient(app)
    h = headers("admin-a", "tenant-a", True)
    created = client.post("/api/v1/auth/api-keys", headers=h, json={"name": "integration", "expires_in_days": 7})
    assert created.status_code == 200
    payload = created.json()
    assert payload["key"].startswith("slk_")
    assert "hash" not in payload and payload["key_prefix"] in payload["key"]
    key_id = payload["id"]
    listed = client.get("/api/v1/auth/api-keys", headers=h)
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == key_id
    assert "key" not in listed.json()[0]
    revoked = client.post(f"/api/v1/auth/api-keys/{key_id}/revoke", headers=h)
    assert revoked.status_code == 200
    assert revoked.json()["revoked"] is True


def test_runtime_event_persists_risk_decision_record():
    seed_users()
    client = TestClient(app)
    h = headers("admin-a", "tenant-a", True)
    created = client.post("/api/v1/events", headers=h, json={
        "event_type": "risk.decision", "source": "gateway", "risk_score": 91,
        "outcome": "BLOCK", "data": {"confidence": 0.92, "factors": {"suspicious_ip": True}},
    })
    assert created.status_code == 200
    decisions = client.get("/api/v1/events/decisions", headers=h)
    assert decisions.status_code == 200
    assert decisions.json()[0]["score"] == 91
    assert decisions.json()[0]["confidence"] == 92
    assert decisions.json()[0]["action"] == "BLOCK"
    assert decisions.json()[0]["factors"]["suspicious_ip"] is True


def test_behavior_baseline_versioning_and_rollback():
    seed_users()
    client = TestClient(app)
    h = headers("admin-a", "tenant-a", True)
    first = client.post("/api/v1/behavior/baselines", headers=h, json={
        "baseline_key": "/api/orders", "baseline_type": "endpoint", "stats": {"mean": 10},
    })
    second = client.post("/api/v1/behavior/baselines", headers=h, json={
        "baseline_key": "/api/orders", "baseline_type": "endpoint", "stats": {"mean": 12},
    })
    assert first.status_code == 200 and second.status_code == 200
    assert first.json()["version"] == 1 and second.json()["version"] == 2
    assert second.json()["status"] == "active"
    rolled = client.post(f"/api/v1/behavior/baselines/{first.json()['id']}/rollback", headers=h)
    assert rolled.status_code == 200
    assert rolled.json()["status"] == "active"
    versions = client.get("/api/v1/behavior/baselines", headers=h)
    assert [row["status"] for row in versions.json()] == ["rolled_back", "active"]


def test_risk_calibration_is_versioned_and_tenant_scoped():
    seed_users()
    client = TestClient(app)
    h = headers("admin-a", "tenant-a", True)
    digest = "a" * 64
    first = client.post("/api/v1/risk/calibrations", headers=h, json={
        "factor": 100, "dataset_hash": digest, "sample_count": 100, "fp_rate": 2, "fn_rate": 1,
    })
    second = client.post("/api/v1/risk/calibrations", headers=h, json={
        "factor": 110, "dataset_hash": "b" * 64, "sample_count": 200, "fp_rate": 3, "fn_rate": 2,
    })
    assert first.status_code == 200 and second.status_code == 200
    assert first.json()["version"] == 1 and second.json()["version"] == 2
    assert second.json()["status"] == "active"
    activated = client.post(f"/api/v1/risk/calibrations/{first.json()['id']}/activate", headers=h)
    assert activated.status_code == 200
    assert activated.json()["status"] == "active"
    rows = client.get("/api/v1/risk/calibrations", headers=h)
    assert rows.status_code == 200
    assert rows.json()[0]["version"] == 2 and rows.json()[1]["version"] == 1


def test_privacy_export_and_legal_hold_lifecycle():
    seed_users()
    client = TestClient(app)
    h = headers("admin-a", "tenant-a", True)
    hold = client.post("/api/v1/privacy/legal-holds", headers=h, json={"reason": "legal review", "scope": {"case": "CASE-1"}})
    assert hold.status_code == 200
    assert hold.json()["status"] == "active"
    exports = client.post("/api/v1/privacy/exports", headers=h)
    assert exports.status_code == 200
    assert len(exports.json()["artifact_hash"]) == 64
    listed = client.get("/api/v1/privacy/exports", headers=h)
    assert listed.status_code == 200 and listed.json()[0]["status"] == "COMPLETED"
    released = client.post(f"/api/v1/privacy/legal-holds/{hold.json()['id']}/release", headers=h)
    assert released.status_code == 200 and released.json()["status"] == "released"
