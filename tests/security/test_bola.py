import pytest
from httpx import AsyncClient
from src.sentinelayer.api.main_full import app

@pytest.mark.asyncio
async def test_auth_middleware():
    client = AsyncClient(app=app, base_url="http://test")
    resp = await client.get("/api/v1/protected")
    assert resp.status_code == 401

@pytest.mark.asyncio
async def test_tenant_isolation():
    client = AsyncClient(app=app, base_url="http://test")
    resp = await client.get("/api/v1/tenants")
    assert resp.status_code == 200
