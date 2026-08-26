from fastapi import APIRouter
import random

router = APIRouter(prefix="/heatmap", tags=["heatmap"])

ENDPOINTS = [
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/tenants",
    "/api/v1/policies",
    "/api/v1/incidents",
    "/api/v1/evidence",
    "/api/v1/metrics",
    "/api/v1/health",
    "/api/v1/controlplane",
]

@router.get("/")
async def get_heatmap():
    return [
        {
            "endpoint": ep,
            "risk": random.randint(0, 100),
            "requests": random.randint(0, 1000),
            "blocks": random.randint(0, 50)
        }
        for ep in ENDPOINTS
    ]
