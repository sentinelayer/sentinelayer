import pytest
import asyncio
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_load_100_requests():
    client = AsyncClient()
    tasks = [client.get("http://localhost:8005/") for _ in range(100)]
    responses = await asyncio.gather(*tasks)
    success_count = sum(1 for r in responses if r.status_code == 200)
    assert success_count > 90
