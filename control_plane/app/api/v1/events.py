from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/events", tags=["events"])

EVENTS: list[dict] = []


class EventCreate(BaseModel):
    event_type: str
    source: str = "system"
    data: dict[str, Any] = Field(default_factory=dict)


@router.get("/")
@router.get("")
async def get_events(limit: int = 50):
    return EVENTS[-limit:]


@router.post("/")
@router.post("")
async def create_event(body: EventCreate):
    event = {
        "id": str(uuid.uuid4()),
        "type": body.event_type,
        "source": body.source,
        "data": body.data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    EVENTS.append(event)
    return event
