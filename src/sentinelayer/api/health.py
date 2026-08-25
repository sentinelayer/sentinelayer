from fastapi import APIRouter, Depends
from sentinelayer.database.models.base import DatabaseManager
import time
import os

router = APIRouter()

@router.get("/health")
async def health():
    return {"status": "healthy", "timestamp": time.time()}

@router.get("/health/readiness")
async def readiness():
    # Check database
    try:
        db = DatabaseManager()
        with db.get_session() as session:
            session.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {e}"
        return {"status": "not_ready", "database": db_status}, 503
    
    # Check Redis
    try:
        import redis
        r = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        r.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {e}"
        return {"status": "not_ready", "redis": redis_status}, 503
    
    return {"status": "ready", "database": db_status, "redis": redis_status}

@router.get("/health/liveness")
async def liveness():
    return {"status": "alive", "timestamp": time.time()}
