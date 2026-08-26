import pytest
from httpx import AsyncClient
from src.sentinelayer.api.main import app

@pytest.mark.asyncio
async def test_waf_sql_injection():
    client = AsyncClient(app=app, base_url="http://test")
    resp = await client.get("/api/v1/risk/calculate?input='; DROP TABLE users; --")
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_waf_xss():
    client = AsyncClient(app=app, base_url="http://test")
    resp = await client.post("/api/v1/risk/calculate", json={"input": "<script>alert(1)</script>"})
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_health():
    client = AsyncClient(app=app, base_url="http://test")
    resp = await client.get("/health")
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_root():
    client = AsyncClient(app=app, base_url="http://test")
    resp = await client.get("/")
    assert resp.status_code == 200
