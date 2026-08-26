import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_full_pipeline():
    client = AsyncClient()
    response = await client.get("http://localhost:8005/")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_auth_flow():
    client = AsyncClient()
    register = await client.post(
        "http://localhost:8005/api/v1/auth/register",
        json={"email": "pipeline@test.com", "password": "pass123", "full_name": "Pipeline User", "tenant_id": "tenant-1"}
    )
    assert register.status_code == 200

    login = await client.post(
        "http://localhost:8005/api/v1/auth/login",
        json={"email": "pipeline@test.com", "password": "pass123"}
    )
    assert login.status_code == 200
    assert "access_token" in login.json()
