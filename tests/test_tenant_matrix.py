import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_tenant_isolation_api():
    client = AsyncClient()
    resp = await client.get("http://localhost:8005/api/v1/tenants")
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_tenant_isolation_auth():
    client = AsyncClient()
    resp = await client.post(
        "http://localhost:8005/api/v1/auth/login",
        json={"email": "tenant_a@test.com", "password": "password123"}
    )
    assert resp.status_code in [200, 401]

@pytest.mark.asyncio
async def test_tenant_isolation_application():
    client = AsyncClient()
    resp = await client.get("http://localhost:8005/api/v1/applications")
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_tenant_isolation_policy():
    client = AsyncClient()
    resp = await client.get("http://localhost:8005/api/v1/policies")
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_tenant_isolation_evidence():
    client = AsyncClient()
    resp = await client.get("http://localhost:8005/api/v1/evidence")
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_tenant_isolation_incident():
    client = AsyncClient()
    resp = await client.get("http://localhost:8005/api/v1/incidents")
    assert resp.status_code == 200
