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


def test_login_rejects_password_suffix_beyond_bcrypt_boundary(registration):
    client, _ = registration
    value = "a" * 72
    assert signup(client, password=value).status_code == 200
    response = client.post("/api/v1/auth/login", json={
        "email": "owner@example.com", "password": value + "suffix",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize("password", [None, "", "short", "é" * 37])
async def test_administrative_user_creation_rejects_missing_password(password):
    """Invalid credentials fail before any database mutation."""
    from fastapi import HTTPException
    from control_plane.app.api.v1.users import UserCreate, create_user

    data = UserCreate(email="invitee@example.com", full_name="Invitee", password=password)
    with pytest.raises(HTTPException) as failure:
        await create_user(data, request=None, db=None)
    assert failure.value.status_code == 400


@pytest.mark.asyncio
async def test_administrative_user_creation_hashes_supplied_password(registration):
    """A successful direct creation must result in a usable login credential."""
    import bcrypt
    from types import SimpleNamespace
    from control_plane.app.api.v1.users import UserCreate, create_user

    _, sessions = registration
    supplied_password = "a" * 12 + "B3!"  # synthetic test credential; never logged
    with sessions() as db:
        db.add(Tenant(id="tenant-direct", name="tenant-direct"))
        db.commit()
        req = SimpleNamespace(state=SimpleNamespace(tenant_id="tenant-direct"))
        result = await create_user(
            UserCreate(email="invitee@example.com", full_name="Invitee",
                       password=supplied_password),
            request=req, db=db,
        )
        created = db.query(User).filter(User.id == result["id"]).one()
        assert bcrypt.checkpw(supplied_password.encode('utf-8'), created.hashed_password.encode())
        assert result["tenant_id"] == "tenant-direct"
        assert "password" not in result
