from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import UTC, datetime
from ipaddress import ip_address
from typing import Any
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import AnyHttpUrl, BaseModel, Field
from sqlalchemy.orm import Session

from control_plane.app.api.deps import db_with_tenant, tenant_id
from control_plane.app.infrastructure.db.models import WebhookDelivery, WebhookRegistration

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class WebhookRegister(BaseModel):
    url: AnyHttpUrl
    events: list[str] = Field(default_factory=list, max_length=100)
    secret: str | None = Field(default=None, min_length=16, max_length=256)


def _validate_url(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in {"http", "https"} or not host:
        raise HTTPException(status_code=400, detail="Webhook URL must use HTTP(S)")
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        raise HTTPException(status_code=400, detail="Private/local webhook targets are not allowed")
    try:
        address = ip_address(host)
    except ValueError:
        address = None
    if address and (address.is_private or address.is_loopback or address.is_link_local or address.is_reserved):
        raise HTTPException(status_code=400, detail="Private webhook targets are not allowed")
    return url


def _secret(data: WebhookRegister) -> str:
    secret = data.secret or os.getenv("WEBHOOK_SECRET")
    if not secret or len(secret) < 16:
        raise HTTPException(status_code=400, detail="Webhook secret must be provided or configured")
    return secret


def _serialize(webhook: WebhookRegistration) -> dict[str, Any]:
    return {
        "id": webhook.id, "tenant_id": webhook.tenant_id, "url": webhook.url,
        "events": json.loads(webhook.events or "[]"), "created_at": webhook.created_at.isoformat(),
        "secret_configured": True,
    }


@router.post("/register")
async def register_webhook(data: WebhookRegister, request: Request, db: Session = Depends(db_with_tenant)):
    url = _validate_url(str(data.url))
    secret = _secret(data)
    webhook = WebhookRegistration(
        id=str(uuid.uuid4()), tenant_id=tenant_id(request), url=url,
        events=json.dumps(data.events), secret_hash=hashlib.sha256(secret.encode()).hexdigest(),
        created_at=datetime.now(UTC),
    )
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    return _serialize(webhook)


@router.get("/")
@router.get("")
async def list_webhooks(request: Request, db: Session = Depends(db_with_tenant)):
    webhooks = db.query(WebhookRegistration).filter(
        WebhookRegistration.tenant_id == tenant_id(request)
    ).order_by(WebhookRegistration.created_at.desc()).all()
    return [_serialize(webhook) for webhook in webhooks]


@router.post("/{wid}/test")
async def test_webhook(wid: str, request: Request, db: Session = Depends(db_with_tenant)):
    webhook = db.query(WebhookRegistration).filter(
        WebhookRegistration.id == wid, WebhookRegistration.tenant_id == tenant_id(request)
    ).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    delivery = WebhookDelivery(
        id=str(uuid.uuid4()), tenant_id=webhook.tenant_id, webhook_id=webhook.id,
        event_type="webhook.test", status="queued", created_at=datetime.now(UTC),
    )
    db.add(delivery)
    db.commit()
    return {"status": "queued", "webhook_id": webhook.id, "delivery_id": delivery.id}


@router.get("/logs")
async def get_webhook_logs(
    request: Request,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(db_with_tenant),
):
    deliveries = db.query(WebhookDelivery).filter(
        WebhookDelivery.tenant_id == tenant_id(request)
    ).order_by(WebhookDelivery.created_at.desc()).limit(limit).all()
    return [{"id": d.id, "webhook_id": d.webhook_id, "event_type": d.event_type,
             "status": d.status, "response_code": d.response_code, "created_at": d.created_at.isoformat()} for d in deliveries]
