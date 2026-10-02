import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from control_plane.app.api.v1.auth import router
from control_plane.app.infrastructure.db.models import Base, Tenant, User
from control_plane.app.infrastructure.db.session import get_db


@pytest.fixture
def registration():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    def db():
        with sessions() as session:
            yield session

    app.dependency_overrides[get_db] = db
    yield TestClient(app), sessions
    engine.dispose()


def signup(client, email="owner@example.com", tenant="tenant-owner", password="StrongPassword123!"):
    return client.post("/api/v1/auth/register", json={
        "email": email, "password": password,
        "full_name": "Test User", "tenant_id": tenant,
    })


def test_public_signup_cannot_join_existing_tenant(registration):
    client, sessions = registration
    assert signup(client).status_code == 200
    response = signup(client, email="outsider@example.com")
    assert response.status_code == 409
    with sessions() as db:
        assert db.query(User).filter(User.email == "outsider@example.com").first() is None
        assert db.query(Tenant).count() == 1


def test_signup_creates_independent_workspaces(registration):
    client, sessions = registration
    assert signup(client).status_code == 200
    assert signup(client, email="second@example.com", tenant="tenant-second").status_code == 200
    with sessions() as db:
        assert {user.tenant_id for user in db.query(User).all()} == {"tenant-owner", "tenant-second"}


@pytest.mark.parametrize("tenant", ["", "tenant.with.dots", "tenant/other", "x" * 129])
def test_signup_rejects_tenant_ids_that_rls_would_rewrite(registration, tenant):
    client, _ = registration
    assert signup(client, tenant=tenant).status_code == 422


def test_signup_rejects_passwords_bcrypt_would_truncate(registration):
    client, _ = registration
    assert signup(client, password="a" * 73).status_code == 400
    assert signup(client, password="é" * 37).status_code == 400


def test_inactive_user_cannot_login(registration):
    client, sessions = registration
    assert signup(client).status_code == 200
    with sessions() as db:
        user = db.query(User).first()
        user.is_active = False
        db.commit()
    response = client.post("/api/v1/auth/login", json={
        "email": "owner@example.com", "password": "StrongPassword123!",
    })
    assert response.status_code == 401
