import secrets

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.app.infrastructure.db.models import Base, User, Tenant
from scripts.setup_pilot import provision_accounts, TENANT


@pytest.fixture
def setup_db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        yield db


@pytest.fixture
def values():
    return {"PILOT_ADMIN_EMAIL": "owner@example.com",
            "PILOT_ADMIN_PASSWORD": secrets.token_hex(24),
            "PILOT_ADMIN_MFA_SECRET": "A" * 32,
            "PILOT_SERVICE_PASSWORD": secrets.token_hex(24),
            "PILOT_GATEWAY_API_KEY": "slk_" + secrets.token_hex(24)}


def test_idempotent_bootstrap_preserves_owner_credentials(setup_db, values):
    admin_id, service_id = provision_accounts(setup_db, values)
    admin = setup_db.get(User, admin_id)
    service = setup_db.get(User, service_id)
    assert admin.is_admin and admin.mfa_enabled and admin.tenant_id == TENANT
    assert not service.is_admin
    admin.hashed_password = "owner-changed-password-hash"
    admin.mfa_secret = "owner-changed-mfa-secret"
    setup_db.commit()
    provision_accounts(setup_db, values)
    assert setup_db.get(User, admin_id).hashed_password == "owner-changed-password-hash"
    assert setup_db.get(User, admin_id).mfa_secret == "owner-changed-mfa-secret"


def test_bootstrap_refuses_existing_email_in_another_workspace(setup_db, values):
    setup_db.add(Tenant(id="other", name="other"))
    setup_db.add(User(id="existing", email=values["PILOT_ADMIN_EMAIL"], tenant_id="other",
                      is_admin=False, hashed_password="existing-hash"))
    setup_db.commit()
    with pytest.raises(ValueError, match="conflicts"):
        provision_accounts(setup_db, values)
    assert not setup_db.get(User, "existing").is_admin
    assert setup_db.get(Tenant, TENANT) is None


def test_invalid_mfa_secret_does_not_create_accounts(setup_db, values):
    values["PILOT_ADMIN_MFA_SECRET"] = "invalid"
    with pytest.raises(ValueError, match="MFA secret"):
        provision_accounts(setup_db, values)
    assert setup_db.query(User).count() == 0
