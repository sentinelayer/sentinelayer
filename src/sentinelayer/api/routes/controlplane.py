from fastapi import APIRouter, Depends
from src.sentinelayer.controlplane import control_plane
from src.sentinelayer.api.middleware.auth import AuthMiddleware

router = APIRouter(prefix="/api/v1/controlplane", tags=["controlplane"])

@router.post("/tenants")
async def create_tenant(name: str):
    return control_plane.create_tenant(name)

@router.get("/tenants")
async def list_tenants():
    return control_plane.get_tenants()
