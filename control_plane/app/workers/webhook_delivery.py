from __future__ import annotations

import hashlib
import hmac
import os
import socket
import uuid
from datetime import UTC, datetime, timedelta
from ipaddress import ip_address
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from sqlalchemy import or_

from control_plane.app.infrastructure.db.models import WebhookDelivery, WebhookRegistration
from control_plane.app.infrastructure.db.session import SessionLocal
from control_plane.app.infrastructure.kms.client import KMSClient

MAX_ATTEMPTS = max(1, int(os.getenv("WEBHOOK_DELIVERY_MAX_ATTEMPTS", "5")))
TIMEOUT_SECONDS = max(1, int(os.getenv("WEBHOOK_DELIVERY_TIMEOUT_SECONDS", "5")))
_kms = KMSClient()


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _safe_addresses(host: str) -> bool:
    try:
        values = {info[4][0] for info in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)}
    except socket.gaierror:
        return False
    for raw in values:
        try:
            address = ip_address(raw)
        except ValueError:
            return False
        if address.is_private or address.is_loopback or address.is_link_local or address.is_reserved or address.is_multicast:
            return False
    return bool(values)


def _deliver(delivery: WebhookDelivery, webhook: WebhookRegistration) -> dict[str, object]:
    host = (urlparse(webhook.url).hostname or "").lower()
    if not host or not _safe_addresses(host):
        raise ValueError("webhook destination does not resolve to a public address")
    secret = _kms.decrypt(webhook.secret_ciphertext or "")
    body = delivery.payload or "{}"
    timestamp = str(int(datetime.now(UTC).timestamp()))
    nonce = uuid.uuid4().hex
    signing_input = f"{timestamp}.{nonce}.{body}".encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).hexdigest()
    req = Request(
        webhook.url, data=body.encode("utf-8"), method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "SentinelLayer-Webhook/1",
            "X-Sentinel-Timestamp": timestamp,
            "X-Sentinel-Nonce": nonce,
            "X-Sentinel-Signature": f"sha256={signature}",
            "X-Sentinel-Delivery": delivery.id,
        },
    )
    try:
        with build_opener(_NoRedirect()).open(req, timeout=TIMEOUT_SECONDS) as response:
            status = response.status
    except HTTPError as exc:
        status = exc.code
    except (URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(str(exc)) from exc
    if not 200 <= status < 300:
        raise RuntimeError(f"webhook returned HTTP {status}")
    delivery.last_signature = f"sha256={signature}"
    delivery.response_code = status
    return {"status": "delivered", "response_code": status, "signature": delivery.last_signature}


def deliver_pending_webhooks(limit: int = 100) -> dict[str, int]:
    db = SessionLocal()
    delivered = retried = dead_letter = 0
    try:
        now = datetime.now(UTC)
        rows = db.query(WebhookDelivery).filter(
            WebhookDelivery.status.in_(["queued", "retry"]),
            or_(WebhookDelivery.next_attempt_at.is_(None), WebhookDelivery.next_attempt_at <= now),
        ).order_by(WebhookDelivery.created_at.asc()).limit(limit).all()
        for delivery in rows:
            webhook = db.query(WebhookRegistration).filter(
                WebhookRegistration.id == delivery.webhook_id,
                WebhookRegistration.tenant_id == delivery.tenant_id,
            ).first()
            delivery.attempt_count = (delivery.attempt_count or 0) + 1
            delivery.status = "delivering"
            db.commit()
            try:
                if not webhook:
                    raise ValueError("webhook registration not found")
                _deliver(delivery, webhook)
                delivery.status = "delivered"
                delivery.last_error = None
                delivered += 1
            except Exception as exc:  # noqa: BLE001 - persist delivery failure and continue queue
                delivery.last_error = str(exc)[:1000]
                if delivery.attempt_count >= MAX_ATTEMPTS:
                    delivery.status = "dead_letter"
                    dead_letter += 1
                else:
                    delivery.status = "retry"
                    delivery.next_attempt_at = datetime.now(UTC) + timedelta(seconds=min(3600, 30 * (2 ** (delivery.attempt_count - 1))))
                    retried += 1
            db.commit()
        return {"delivered": delivered, "retried": retried, "dead_letter": dead_letter}
    finally:
        db.close()
