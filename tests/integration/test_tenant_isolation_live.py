"""Live tenant isolation — requires CONTROL_PLANE_URL + JWT_SECRET + DB."""
from __future__ import annotations

import os
import uuid

import pytest
from httpx import AsyncClient

BASE = os.getenv("CONTROL_PLANE_URL", "http://localhost:8005")


def _uid() -> str:
    return uuid.uuid4().hex[:10]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cross_tenant_application_denied():
    async with AsyncClient(base_url=BASE, timeout=20.0) as client:
        try:
            h = await client.get("/health")
            if h.status_code >= 500:
                pytest.skip("control plane unhealthy")
        except Exception:
            pytest.skip("control plane unreachable")

        ta, tb = f"ta-{_uid()}", f"tb-{_uid()}"
        ea, eb = f"{ta}@test.local", f"{tb}@test.local"
        password = "TestPass12chars!"

        ra = await client.post("/api/v1/auth/register", json={"email": ea, "password": password, "full_name": "A", "tenant_id": ta})
        rb = await client.post("/api/v1/auth/register", json={"email": eb, "password": password, "full_name": "B", "tenant_id": tb})
        assert ra.status_code in (200, 201, 400), ra.text
        assert rb.status_code in (200, 201, 400), rb.text

        la = await client.post("/api/v1/auth/login", json={"email": ea, "password": password})
        lb = await client.post("/api/v1/auth/login", json={"email": eb, "password": password})
        if la.status_code != 200 or lb.status_code != 200:
            pytest.skip(f"login failed: {la.status_code} {lb.status_code}")

        token_a = la.json()["access_token"]
        token_b = lb.json()["access_token"]
        ha = {"Authorization": f"Bearer {token_a}", "X-Tenant-ID": ta}
        hb = {"Authorization": f"Bearer {token_b}", "X-Tenant-ID": tb}

        create = await client.post("/api/v1/applications", headers=ha, json={"name": f"app-{_uid()}", "environment": "production"})
        assert create.status_code in (200, 201), create.text
        obj_id = create.json()["id"]

        # B must not see A's app
        get_b = await client.get(f"/api/v1/applications/{obj_id}", headers=hb)
        assert get_b.status_code in (403, 404), f"BOLA leak: {get_b.status_code} {get_b.text}"

        list_b = await client.get("/api/v1/applications", headers=hb)
        assert list_b.status_code == 200
        ids = [x.get("id") for x in list_b.json()]
        assert obj_id not in ids
