import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_http_desync_protection():
    client = AsyncClient()
    headers = {
        "Transfer-Encoding": "chunked",
        "Content-Length": "100",
    }
    response = await client.post(
        "http://localhost:8005/api/v1/auth/login",
        headers=headers,
        content="0\r\n\r\n"
    )
    assert response.status_code in [400, 403, 429]
