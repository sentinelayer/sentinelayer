from fastapi import APIRouter
from datetime import datetime
import uuid
import random

router = APIRouter(prefix="/events", tags=["events"])

EVENTS = []

@router.get("/")
async def get_events(limit: int = 50):
    return EVENTS[-limit:]

@router.post("/")
async def create_event(event_type: str, source: str = "system", data: dict = None):
    event = {
        "id": str(uuid.uuid4()),
        "type": event_type,
        "source": source,
        "data": data or {},
        "timestamp": datetime.utcnow().isoformat()
    }
    EVENTS.append(event)
    return event
