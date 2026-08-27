from datetime import UTC, datetime, timedelta

import jwt
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from control_plane.app.middleware.auth import AuthMiddleware
from control_plane.app.middleware.rbac import RBACMiddleware
from control_plane.app.middleware.tenant import TenantMiddleware


SECRET = "audit-secret-minimum-32-characters"


def make_client() -> TestClient:
    app = FastAPI()

    @app.get("/protected")
    async def protected(request: Request):
        return {"tenant_id": request.state.tenant_id}

    @app.get("/api/v1/admin/high-risk-actions")
    async def admin_route():
        return {"ok": True}

    # Add inner-to-outer: tenant, RBAC, auth.
    app.add_middleware(TenantMiddleware)
    app.add_middleware(RBACMiddleware)
    app.add_middleware(AuthMiddleware)
    return TestClient(app)


def token(*, tenant_id: str = "tenant-a", is_admin: bool = False) -> str:
    return jwt.encode(
        {
            "sub": "user-a",
            "tenant_id": tenant_id,
            "is_admin": is_admin,
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        SECRET,
        algorithm="HS256",
    )


def test_protected_path_requires_jwt(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", SECRET)
    response = make_client().get("/protected")
    assert response.status_code == 401


def test_tenant_header_must_match_jwt(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", SECRET)
    response = make_client().get(
        "/protected",
        headers={"Authorization": f"Bearer {token()}", "X-Tenant-ID": "tenant-b"},
    )
    assert response.status_code == 403


def test_admin_path_rejects_normal_user(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", SECRET)
    response = make_client().get(
        "/api/v1/admin/high-risk-actions",
        headers={"Authorization": f"Bearer {token()}"},
    )
    assert response.status_code == 403


def test_authenticated_tenant_context_is_available_without_header(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", SECRET)
    response = make_client().get("/protected", headers={"Authorization": f"Bearer {token()}"})
    assert response.status_code == 200
    assert response.json() == {"tenant_id": "tenant-a"}
