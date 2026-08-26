import pytest
from httpx import AsyncClient
@pytest.mark.asyncio
async def test_sql_injection_blocked():
    client = AsyncClient()
    response = await client.get("http://localhost:8005/api/v1/metrics/security?input='; DROP TABLE users; --")
    assert response.status_code == 403
