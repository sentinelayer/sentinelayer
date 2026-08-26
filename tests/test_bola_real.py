import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_tenant_a_cant_access_tenant_b():
    client = AsyncClient()
    
    # Register Tenant A
    resp = await client.post(
        "http://localhost:8005/api/v1/auth/register",
        json={"email": "tenanta@test.com", "password": "pass123", "full_name": "Tenant A", "tenant_id": "tenant-a-001"}
    )
    assert resp.status_code == 200
    
    # Register Tenant B
    resp = await client.post(
        "http://localhost:8005/api/v1/auth/register",
        json={"email": "tenantb@test.com", "password": "pass123", "full_name": "Tenant B", "tenant_id": "tenant-b-002"}
    )
    assert resp.status_code == 200
    
    # Login Tenant A
    resp = await client.post(
        "http://localhost:8005/api/v1/auth/login",
        json={"email": "tenanta@test.com", "password": "pass123"}
    )
    token_a = resp.json()["access_token"]
    
    # Login Tenant B
    resp = await client.post(
        "http://localhost:8005/api/v1/auth/login",
        json={"email": "tenantb@test.com", "password": "pass123"}
    )
    token_b = resp.json()["access_token"]
    
    # Tenant A creates tenant
    headers_a = {"Authorization": f"Bearer {token_a}", "X-Tenant-ID": "tenant-a-001"}
    resp = await client.post(
        "http://localhost:8005/api/v1/tenants",
        headers=headers_a,
        json={"name": "Tenant A's Tenant"}
    )
    assert resp.status_code == 200
    
    # Tenant B tries to access Tenant A's tenant - SHOULD FAIL
    headers_b = {"Authorization": f"Bearer {token_b}", "X-Tenant-ID": "tenant-b-002"}
    resp = await client.get("http://localhost:8005/api/v1/tenants", headers=headers_b)
    # Should not see Tenant A's tenant
    tenants = resp.json()
    tenant_names = [t["name"] for t in tenants]
    assert "Tenant A's Tenant" not in tenant_names
