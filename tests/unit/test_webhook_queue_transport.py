"""Real queue, encryption, signature and HTTP delivery/retry in an isolated test."""
import hashlib
import hmac
import threading
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from control_plane.app.infrastructure.db.models import Base, Tenant, WebhookRegistration, WebhookDelivery
from control_plane.app.workers import webhook_delivery as worker


def test_queue_retry_to_signed_receiver_and_persisted_completion(tmp_path, monkeypatch):
    secret = "test-local-webhook-secret"
    received = []
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = self.rfile.read(int(self.headers["Content-Length"]))
            signing_input = self.headers["X-Sentinel-Timestamp"].encode() + b"." + self.headers["X-Sentinel-Nonce"].encode() + b"." + body
            valid = hmac.compare_digest(self.headers["X-Sentinel-Signature"], "sha256=" + hmac.new(secret.encode(), signing_input, hashlib.sha256).hexdigest())
            received.append({"valid": valid, "id": self.headers["X-Sentinel-Delivery"], "body": body})
            self.send_response(503 if len(received) == 1 else 202 if valid else 401)
            self.end_headers()
        def log_message(self, *_args): pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    engine = create_engine(f"sqlite:///{tmp_path / 'queue.db'}")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    monkeypatch.setattr(worker, "SessionLocal", sessions)
    # Only destination validation is replaced to reach the isolated receiver.
    # Production still rejects loopback; HTTP, encryption, HMAC and SQL are real.
    monkeypatch.setattr(worker, "_resolve_public_addresses", lambda _host: ("127.0.0.1",))
    try:
        with sessions() as db:
            db.add(Tenant(id="local", name="local")); db.flush()
            db.add(WebhookRegistration(id="hook", tenant_id="local", url=f"http://receiver.example.test:{server.server_port}/events", secret_ciphertext=worker._kms.encrypt(secret), secret_hash=hashlib.sha256(secret.encode()).hexdigest())); db.flush()
            db.add(WebhookDelivery(id="delivery", tenant_id="local", webhook_id="hook", event_type="test", payload='{"event":"test"}', status="queued", attempt_count=0)); db.commit()
        assert worker.deliver_pending_webhooks() == {"delivered": 0, "retried": 1, "dead_letter": 0}
        with sessions() as db:
            row = db.get(WebhookDelivery, "delivery")
            assert row.status == "retry" and row.attempt_count == 1
            row.next_attempt_at = datetime.now(UTC) - timedelta(seconds=1)
            db.commit()
        assert worker.deliver_pending_webhooks() == {"delivered": 1, "retried": 0, "dead_letter": 0}
        assert worker.deliver_pending_webhooks() == {"delivered": 0, "retried": 0, "dead_letter": 0}
        with sessions() as db:
            row = db.get(WebhookDelivery, "delivery")
            assert row.status == "delivered" and row.attempt_count == 2
            assert row.response_code == 202 and row.next_attempt_at is None
        assert received == [{"valid": True, "id": "delivery", "body": b'{"event":"test"}'}] * 2
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=5)
        engine.dispose()
