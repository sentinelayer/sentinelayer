from __future__ import annotations

import hashlib
import hmac
import http.client
import os
import socket
import uuid
from datetime import UTC, datetime, timedelta
from ipaddress import ip_address
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPHandler, HTTPSHandler, HTTPRedirectHandler, ProxyHandler, Request, build_opener

from sqlalchemy import and_, or_

from control_plane.app.infrastructure.db.models import WebhookDelivery, WebhookRegistration
from control_plane.app.infrastructure.db.session import WorkerSessionLocal as SessionLocal
from control_plane.app.infrastructure.kms.client import KMSClient

MAX_ATTEMPTS = max(1, int(os.getenv("WEBHOOK_DELIVERY_MAX_ATTEMPTS", "5")))
TIMEOUT_SECONDS = max(1, int(os.getenv("WEBHOOK_DELIVERY_TIMEOUT_SECONDS", "5")))
_kms = KMSClient()


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _resolve_public_addresses(host: str) -> tuple[str, ...]:
    try:
        values = {info[4][0] for info in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)}
    except socket.gaierror:
        return ()
    for raw in values:
        try:
            address = ip_address(raw)
        except ValueError:
            return ()
        if not address.is_global or address.is_multicast:
            return ()
    return tuple(sorted(values))


def _safe_addresses(host: str) -> bool:
    return bool(_resolve_public_addresses(host))


def _connect_pinned(addresses, destination, timeout, source_address=None):
    """Connect only to validated numeric IPs; never resolve the hostname again."""
    port = destination[1]
    last_error = None
    for raw in addresses:
        family = socket.AF_INET6 if ip_address(raw).version == 6 else socket.AF_INET
        sock = socket.socket(family, socket.SOCK_STREAM)
        try:
            sock.settimeout(timeout)
            if source_address:
                sock.bind(source_address)
            sock.connect((raw, port))
            return sock
        except OSError as exc:
            last_error = exc
            sock.close()
    raise last_error or OSError("No validated webhook addresses")


def _connection(connection_type, addresses, host, **kwargs):
    connection = connection_type(host, **kwargs)
    # HTTPSConnection retains the original host for certificate checks and SNI.
    connection._create_connection = lambda destination, timeout, source_address=None: _connect_pinned(
        addresses, destination, timeout, source_address,
    )
    return connection


class _PinnedHTTPHandler(HTTPHandler):
    def __init__(self, addresses):
        super().__init__()
        self.addresses = addresses

    def http_open(self, req):
        return self.do_open(lambda host, **kwargs: _connection(
            http.client.HTTPConnection, self.addresses, host, **kwargs,
        ), req)


class _PinnedHTTPSHandler(HTTPSHandler):
    def __init__(self, addresses):
        super().__init__()
        self.addresses = addresses

    def https_open(self, req):
        return self.do_open(lambda host, **kwargs: _connection(
            http.client.HTTPSConnection, self.addresses, host, **kwargs,
        ), req, context=self._context)


def _deliver(delivery: WebhookDelivery, webhook: WebhookRegistration) -> dict[str, object]:
    parsed = urlparse(webhook.url)
    host = (parsed.hostname or "").lower()
    addresses = _resolve_public_addresses(host) if host and parsed.scheme in {"http", "https"} else ()
    if not addresses:
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
        with build_opener(ProxyHandler({}), _NoRedirect(), _PinnedHTTPHandler(addresses),
                          _PinnedHTTPSHandler(addresses)).open(req, timeout=TIMEOUT_SECONDS) as response:
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


def _eligible(now):
    due = or_(WebhookDelivery.next_attempt_at.is_(None), WebhookDelivery.next_attempt_at <= now)
    expired = or_(
        WebhookDelivery.next_attempt_at <= now,
        and_(WebhookDelivery.next_attempt_at.is_(None),
             WebhookDelivery.created_at <= now - timedelta(minutes=5)),
    )
    return or_(and_(WebhookDelivery.status.in_(["queued", "retry"]), due),
               and_(WebhookDelivery.status == "delivering", expired))


def _claim(db, delivery, now):
    query = db.query(WebhookDelivery).filter(WebhookDelivery.id == delivery.id, _eligible(now))
    exhausted = query.filter(WebhookDelivery.attempt_count >= MAX_ATTEMPTS).update({
        "status": "dead_letter", "last_error": "delivery attempt budget exhausted after interrupted claim",
        "next_attempt_at": None,
    }, synchronize_session=False)
    if exhausted:
        db.commit()
        return "dead_letter"
    claimed = query.filter(WebhookDelivery.attempt_count < MAX_ATTEMPTS).update({
        "status": "delivering", "attempt_count": WebhookDelivery.attempt_count + 1,
        "next_attempt_at": now + timedelta(seconds=max(60, TIMEOUT_SECONDS * 4)),
    }, synchronize_session=False)
    db.commit()
    if not claimed:
        return "skipped"
    db.refresh(delivery)
    return "claimed"


def deliver_pending_webhooks(limit: int = 100) -> dict[str, int]:
    db = SessionLocal()
    delivered = retried = dead_letter = 0
    try:
        now = datetime.now(UTC)
        rows = db.query(WebhookDelivery).filter(
            _eligible(now),
        ).order_by(WebhookDelivery.created_at.asc()).limit(limit).all()
        for delivery in rows:
            claimed = _claim(db, delivery, datetime.now(UTC))
            if claimed == "dead_letter":
                dead_letter += 1
                continue
            if claimed != "claimed":
                continue
            webhook = db.query(WebhookRegistration).filter(
                WebhookRegistration.id == delivery.webhook_id,
                WebhookRegistration.tenant_id == delivery.tenant_id,
            ).first()
            try:
                if not webhook:
                    raise ValueError("webhook registration not found")
                _deliver(delivery, webhook)
                delivery.status = "delivered"
                delivery.last_error = None
                delivery.next_attempt_at = None
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
