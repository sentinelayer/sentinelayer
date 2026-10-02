"""Live API smoke tests against an explicitly running disposable control plane."""
import os
import uuid

import pytest
from httpx import AsyncClient

BASE = os.getenv("CONTROL_PLANE_URL", "http://localhost:8005")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_pipeline():
    async with AsyncClient(base_url=BASE) as client:
        response = await client.get("/health")
        assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_auth_flow():
    suffix = uuid.uuid4().hex
    email = f"pipeline-{suffix}@example.com"
    password = "PipelineTestPassword123!"
    async with AsyncClient(base_url=BASE) as client:
        register = await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "full_name": "Pipeline User", "tenant_id": f"pipeline-{suffix}"}
        )
        assert register.status_code == 200, register.text
        login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert login.status_code == 200, login.text
        assert login.json()["access_token"]
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        assert (await client.get("/api/v1/applications", headers=headers)).status_code == 200
        assert (await client.post("/api/v1/auth/logout", headers=headers)).status_code == 200
        assert (await client.get("/api/v1/applications", headers=headers)).status_code == 401
