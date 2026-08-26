import pytest
from httpx import AsyncClient
from src.sentinelayer.api.main import app

@pytest.mark.asyncio
async def test_tenant_isolation():
    client = AsyncClient(app=app, base_url="http://test")

    resp = await client.post("/api/v1/auth/register", json={
        "email": "tenant_a@test.com",
        "password": "password123",
        "full_name": "Tenant A",
        "tenant_id": "tenant-a-111"
    })
    assert resp.status_code == 201

    resp = await client.post("/api/v1/auth/register", json={
        "email": "tenant_b@test.com",
        "password": "password123",
        "full_name": "Tenant B",
        "tenant_id": "tenant-b-222"
    })
    assert resp.status_code == 201

    resp = await client.post("/api/v1/auth/login", json={
        "email": "tenant_a@test.com",
        "password": "password123"
    })
    token_a = resp.json()["access_token"]

    resp = await client.post("/api/v1/auth/login", json={
        "email": "tenant_b@test.com",
        "password": "password123"
    })
    token_b = resp.json()["access_token"]

    headers_a = {"Authorization": f"Bearer {token_a}", "X-Tenant-ID": "tenant-a-111"}
    headers_b = {"Authorization": f"Bearer {token_b}", "X-Tenant-ID": "tenant-b-222"}

    resp = await client.get("/api/v1/controlplane/tenants", headers=headers_a)
    assert resp.status_code == 200
    tenants = resp.json()
    tenant_ids = [t["id"] for t in tenants]
    assert "tenant-b-222" not in tenant_ids
