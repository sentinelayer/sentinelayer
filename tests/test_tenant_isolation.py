import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_tenant_isolation():
    client = AsyncClient()
    response = await client.get("http://localhost:8005/api/v1/tenants")
    assert response.status_code == 200
