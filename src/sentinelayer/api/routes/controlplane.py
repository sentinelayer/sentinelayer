from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/controlplane", tags=["controlplane"])

@router.get("/tenants")
async def list_tenants():
    return [{"id": "1", "name": "Tenant A"}]
