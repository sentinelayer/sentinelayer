from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {"status": "healthy", "service": "control-plane"}


@router.get("/health/readiness")
async def readiness():
    return {"status": "ready"}
