import pytest
from httpx import AsyncClient
from src.sentinelayer.api.main import app

@pytest.mark.asyncio
async def test_chaos_request():
    client = AsyncClient(app=app, base_url="http://test")
    resp = await client.get("/")
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_chaos_malformed():
    client = AsyncClient(app=app, base_url="http://test")
    resp = await client.post("/api/v1/auth/login", json={"malformed": "data"})
    assert resp.status_code == 400 or resp.status_code == 422
