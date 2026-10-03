"""One-off, explicitly enabled pilot bootstrap using isolated owner credentials.

Secrets are injected by the platform and never returned. Existing credentials
are never reset. Policies and gateway registrations use the authenticated API.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime, timedelta
import uuid
from urllib.parse import urlparse

import bcrypt
import httpx
import pyotp
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.app.infrastructure.db.models import ApiKeyRecord, Tenant, User
from control_plane.app.domain.policy.signing import PolicySigning

TENANT = "sentinel-pilot"
APPLICATION_NAME = "SentinelLayer owned pilot"
POLICY_NAME = "Owned pilot signed gateway policy"
GATEWAY = "railway-pilot-edge-01"
DENY = "/__sentinel_policy_probe__"


def provision_accounts(db: Session, values: dict[str, str]) -> tuple[str, str]:
    email = values["PILOT_ADMIN_EMAIL"].strip().lower()
    password = values["PILOT_ADMIN_PASSWORD"]
    mfa = values["PILOT_ADMIN_MFA_SECRET"]
    service_password = values["PILOT_SERVICE_PASSWORD"]
    raw_key = values["PILOT_GATEWAY_API_KEY"]
    if not email or "@" not in email:
        raise ValueError("Admin email required")
    for secret in (password, service_password):
        if not 24 <= len(secret.encode()) <= 72:
            raise ValueError("Invalid platform-generated password length")
    if len(mfa) != 32 or any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567" for c in mfa):
        raise ValueError("Invalid MFA secret")
    if not raw_key.startswith("slk_") or len(raw_key) < 40:
        raise ValueError("Invalid service key")
    admin_id = str(uuid.uuid5(uuid.NAMESPACE_URL, "sentinel-pilot-admin:" + email))
    service_id = str(uuid.uuid5(uuid.NAMESPACE_URL, "sentinel-pilot-gateway-service"))
    admin = db.query(User).filter(User.email == email).first()
    service_email = "gateway-pilot@sentinelayer.example.com"
    service = db.query(User).filter(User.email == service_email).first()
    # Refuse adoption/elevation of a pre-existing account from another bootstrap.
    if admin and (admin.id != admin_id or admin.tenant_id != TENANT or not admin.is_admin or not admin.is_active):
        raise ValueError("Admin account conflicts with bootstrap identity")
    if service and (service.id != service_id or service.tenant_id != TENANT or service.is_admin or not service.is_active):
        raise ValueError("Service account conflicts with bootstrap identity")
    if not db.get(Tenant, TENANT):
        db.add(Tenant(id=TENANT, name="SentinelLayer owned pilot"))
        db.flush()
    if not admin:
        db.add(User(id=admin_id, email=email, full_name="Pilot owner",
                    tenant_id=TENANT, is_admin=True, is_active=True,
                    hashed_password=bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
                    mfa_enabled=True, mfa_secret=mfa))
    if not service:
        db.add(User(id=service_id, email=service_email, full_name="Gateway policy service",
                    tenant_id=TENANT, is_admin=False, is_active=True,
                    hashed_password=bcrypt.hashpw(service_password.encode(), bcrypt.gensalt()).decode(),
                    mfa_enabled=False))
    db.flush()
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key = db.query(ApiKeyRecord).filter(ApiKeyRecord.key_hash == key_hash).first()
    if key:
        if key.user_id != service_id or key.tenant_id != TENANT or key.revoked_at or (
                key.expires_at and key.expires_at.replace(tzinfo=UTC) <= datetime.now(UTC)):
            raise ValueError("Service key conflicts or has expired")
    else:
        db.add(ApiKeyRecord(name="Pilot gateway policy fetch and receipt", key_prefix=raw_key[:12],
                            key_hash=key_hash, user_id=service_id, tenant_id=TENANT,
                            expires_at=datetime.now(UTC) + timedelta(days=90)))
    db.commit()
    return admin_id, service_id


def main() -> None:
    if os.getenv("SL_PILOT_BOOTSTRAP") != "1":
        raise ValueError("Pilot bootstrap is not explicitly enabled")
    base = os.environ["PILOT_BASE_URL"].rstrip("/")
    parsed = urlparse(base)
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.path:
        raise ValueError("Pilot API origin must be HTTPS without path or credentials")
    with Session(create_engine(os.environ["MIGRATION_DATABASE_URL"])) as db:
        admin_id, service_id = provision_accounts(db, dict(os.environ))
    print("Pilot owner with MFA and non-admin service account provisioned", flush=True)
    with httpx.Client(base_url=base, timeout=20, follow_redirects=False, trust_env=False) as client:
        def api(method, path, data=None):
            response = client.request(method, "/api/v1" + path, json=data)
            if response.status_code != 200:
                raise RuntimeError(f"API {method} {path} status {response.status_code}")
            return response.json()
        login_data = {"email": os.environ["PILOT_ADMIN_EMAIL"], "password": os.environ["PILOT_ADMIN_PASSWORD"]}
        missing_mfa = api("POST", "/auth/login", login_data)
        if not missing_mfa.get("mfa_required") or missing_mfa.get("access_token"):
            raise ValueError("Owner MFA challenge was bypassed")
        login_data["mfa_code"] = pyotp.TOTP(os.environ["PILOT_ADMIN_MFA_SECRET"]).now()
        logged_in = api("POST", "/auth/login", login_data)
        client.headers["Authorization"] = "Bearer " + logged_in["access_token"]
        try:
            owner = api("GET", "/auth/me")
            if owner["id"] != admin_id:
                raise ValueError("Unexpected authenticated owner")
            applications = api("GET", "/applications")
            application = next((a for a in applications if a["name"] == APPLICATION_NAME), None)
            if not application:
                application = api("POST", "/applications", {"name": APPLICATION_NAME})
            policies = api("GET", "/policies")
            policy = next((p for p in policies if p["name"] == POLICY_NAME), None)
            if not policy:
                policy = api("POST", "/policies", {"name": POLICY_NAME, "application_id": application["id"],
                             "rules": {"gateway": {"mode": "enforce", "block_score": 80,
                                                    "deny_path_prefixes": [DENY]}}})
            policy_id = policy["id"]
            api("POST", f"/policies/{policy_id}/gateways",
                {"gateway_id": GATEWAY, "service_user_id": service_id})
            print("Owner MFA login and authenticated policy/gateway registration PASS", flush=True)
            # Public signing material comes from the trusted deployment, never policy responses.
            signer = PolicySigning()
            print("PILOT_PUBLIC_CONFIG=" + json.dumps({"tenant_id": TENANT, "policy_id": policy_id,
                  "gateway_id": GATEWAY, "service_user_id": service_id,
                  "public_keys": {signer.key_id: signer.get_public_key()}, "deny_probe": DENY}), flush=True)
        finally:
            api("POST", "/auth/logout", {})
    print("Pilot bootstrap completed; owner session revoked", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Pilot bootstrap failed: {type(error).__name__}; credentials withheld", flush=True)
        raise SystemExit(1) from None
