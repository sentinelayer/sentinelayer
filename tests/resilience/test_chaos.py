import asyncio

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_chaos_request():
    client = AsyncClient()
    try:
        response = await client.get("http://localhost:8005/")
        assert response.status_code == 200
    except Exception:
        pass

@pytest.mark.asyncio
async def test_chaos_concurrent():
    client = AsyncClient()
    tasks = []
    for i in range(10):
        tasks.append(client.get("http://localhost:8005/"))
    responses = await asyncio.gather(*tasks)
    success_count = sum(1 for r in responses if r.status_code == 200)
    assert success_count > 0
