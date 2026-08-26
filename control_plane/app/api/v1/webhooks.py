import os
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class WebhookRegister(BaseModel):
    url: str
    events: list[str] = Field(default_factory=list)
    secret: str | None = None


WEBHOOKS: dict[str, dict] = {}
WEBHOOK_LOGS: list[dict] = []


@router.post("/register")
async def register_webhook(data: WebhookRegister):
    wid = str(uuid.uuid4())
    WEBHOOKS[wid] = {
        "id": wid,
        "url": data.url,
        "events": data.events,
        "secret": data.secret or os.getenv("WEBHOOK_SECRET", "default-secret"),
        "created_at": datetime.now(UTC).isoformat(),
    }
    return WEBHOOKS[wid]


@router.get("/")
@router.get("")
async def list_webhooks():
    return list(WEBHOOKS.values())


@router.post("/{wid}/test")
async def test_webhook(wid: str):
    if wid not in WEBHOOKS:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {"status": "test_sent", "webhook_id": wid}


@router.get("/logs")
async def get_webhook_logs():
    return WEBHOOK_LOGS[-100:]
