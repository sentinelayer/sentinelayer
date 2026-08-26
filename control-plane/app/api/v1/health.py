from fastapi import APIRouter
from sqlalchemy import text
from src.sentinelayer.database import SessionLocal

router = APIRouter(tags=["health"])

@router.get("/health")
async def health():
    return {"status": "healthy"}

@router.get("/health/readiness")
async def readiness():
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "ready"}
    except Exception as e:
        return {"status": "not_ready", "error": str(e)}
