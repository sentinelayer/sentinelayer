from fastapi import APIRouter, Depends
from sentinelayer.database.models.base import DatabaseManager
import time

router = APIRouter()

@router.get("/")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "sentinelayer"
    }

@router.get("/db")
async def db_health():
    """Check database connectivity"""
    try:
        db = DatabaseManager()
        with db.get_session() as session:
            session.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "error", "error": str(e)}
