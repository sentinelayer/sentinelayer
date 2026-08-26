import pytest
from httpx import AsyncClient
from src.sentinelayer.api.main_full import app

@pytest.mark.asyncio
async def test_waf_sql_injection():
    client = AsyncClient(app=app, base_url="http://test")
    resp = await client.get("/api/v1/orders/?search='; DROP TABLE users; --")
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_waf_xss():
    client = AsyncClient(app=app, base_url="http://test")
    resp = await client.post("/api/v1/orders/", json={"name": "<script>alert(1)</script>"})
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_ssrf_protection():
    client = AsyncClient(app=app, base_url="http://test")
    resp = await client.get("/api/v1/proxy?url=http://169.254.169.254/latest/meta-data")
    assert resp.status_code == 403
