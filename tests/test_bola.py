import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_bola_prevention():
    client = AsyncClient()
    resp = await client.get("http://localhost:8005/api/v1/tenants")
    assert resp.status_code == 200
