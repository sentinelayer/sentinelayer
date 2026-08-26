from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import hmac
import hashlib
import os
from datetime import datetime
import uuid

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

class WebhookRegister(BaseModel):
    url: str
    events: list
    secret: str = None

WEBHOOKS = {}
WEBHOOK_LOGS = []

@router.post("/register")
async def register_webhook(data: WebhookRegister):
    id = str(uuid.uuid4())
    WEBHOOKS[id] = {
        "id": id,
        "url": data.url,
        "events": data.events,
        "secret": data.secret or os.getenv("WEBHOOK_SECRET", "default-secret"),
        "created_at": datetime.utcnow().isoformat()
    }
    return WEBHOOKS[id]

@router.get("/")
async def list_webhooks():
    return list(WEBHOOKS.values())

@router.post("/{id}/test")
async def test_webhook(id: str):
    if id not in WEBHOOKS:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {"status": "test_sent", "webhook_id": id}

@router.get("/logs")
async def get_webhook_logs():
    return WEBHOOK_LOGS[-100:]
