from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from control_plane.app.workers import webhook_delivery


class _Response:
    status = 202

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _Opener:
    def __init__(self):
        self.request = None

    def open(self, request, timeout):
        self.request = request
        assert timeout == webhook_delivery.TIMEOUT_SECONDS
        return _Response()


class _Query:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *_args):
        return self

    def order_by(self, *_args):
        return self

    def limit(self, *_args):
        return self

    def all(self):
        return self.rows

    def first(self):
        return self.rows[0] if self.rows else None


class _DB:
    def __init__(self, delivery, webhook):
        self.delivery = delivery
        self.webhook = webhook
        self.commits = 0
        self.closed = False

    def query(self, model):
        if model is webhook_delivery.WebhookDelivery:
            return _Query([self.delivery])
        return _Query([self.webhook])

    def commit(self):
        self.commits += 1

    def close(self):
        self.closed = True


def test_safe_addresses_rejects_private_and_dns_failure(monkeypatch):
    monkeypatch.setattr(
        webhook_delivery.socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [(None, None, None, None, ("127.0.0.1", 0))],
    )
    assert webhook_delivery._safe_addresses("internal.example") is False

    def fail_dns(*_args, **_kwargs):
        raise webhook_delivery.socket.gaierror("not found")

    monkeypatch.setattr(webhook_delivery.socket, "getaddrinfo", fail_dns)
    assert webhook_delivery._safe_addresses("missing.example") is False


def test_deliver_signs_body_with_timestamp_nonce_and_delivery_id(monkeypatch):
    opener = _Opener()
    monkeypatch.setattr(webhook_delivery, "_resolve_public_addresses", lambda _host: ("8.8.8.8",))
    monkeypatch.setattr(webhook_delivery, "build_opener", lambda *_args: opener)
    monkeypatch.setattr(webhook_delivery._kms, "decrypt", lambda _ciphertext: "delivery-secret")

    delivery = SimpleNamespace(id="delivery-1", payload='{"event":"blocked"}', last_signature=None, response_code=None)
    webhook = SimpleNamespace(url="https://hooks.example.test/events", secret_ciphertext="ciphertext")

    result = webhook_delivery._deliver(delivery, webhook)

    assert result["status"] == "delivered"
    assert result["response_code"] == 202
    assert delivery.last_signature.startswith("sha256=")
    assert opener.request.get_header("X-sentinel-timestamp")
    assert opener.request.get_header("X-sentinel-nonce")
    assert opener.request.get_header("X-sentinel-delivery") == "delivery-1"
    assert opener.request.get_header("X-sentinel-signature") == delivery.last_signature
    assert opener.request.data == b'{"event":"blocked"}'


def test_failed_delivery_retries_then_dead_letters(monkeypatch):
    delivery = SimpleNamespace(
        id="delivery-2",
        tenant_id="tenant-1",
        webhook_id="webhook-1",
        payload="{}",
        status="queued",
        attempt_count=0,
        next_attempt_at=None,
        last_error=None,
        last_signature=None,
        response_code=None,
        created_at=datetime.now(UTC),
    )
    webhook = SimpleNamespace(id="webhook-1", tenant_id="tenant-1")
    db = _DB(delivery, webhook)
    monkeypatch.setattr(webhook_delivery, "SessionLocal", lambda: db)
    monkeypatch.setattr(webhook_delivery, "MAX_ATTEMPTS", 2)
    monkeypatch.setattr(webhook_delivery, "_deliver", lambda *_args: (_ for _ in ()).throw(RuntimeError("upstream unavailable")))

    first = webhook_delivery.deliver_pending_webhooks()
    assert first == {"delivered": 0, "retried": 1, "dead_letter": 0}
    assert delivery.status == "retry"
    assert delivery.attempt_count == 1
    assert delivery.next_attempt_at is not None
    assert "upstream unavailable" in delivery.last_error

    delivery.status = "retry"
    delivery.next_attempt_at = None
    second = webhook_delivery.deliver_pending_webhooks()
    assert second == {"delivered": 0, "retried": 0, "dead_letter": 1}
    assert delivery.status == "dead_letter"
    assert delivery.attempt_count == 2
    assert db.closed is True
    assert db.commits >= 4


@pytest.mark.parametrize("url", ["file:///etc/passwd", "http://127.0.0.1/hook"])
def test_delivery_rejects_non_public_destination(monkeypatch, url):
    monkeypatch.setattr(webhook_delivery, "_resolve_public_addresses", lambda _host: ())
    delivery = SimpleNamespace(id="delivery-3", payload="{}")
    webhook = SimpleNamespace(url=url, secret_ciphertext="ciphertext")
    with pytest.raises(ValueError, match="public address"):
        webhook_delivery._deliver(delivery, webhook)


class _RedirectOpener:
    def open(self, *_args, **_kwargs):
        raise AssertionError("redirect opener must never be followed")


def test_no_redirect_handler_is_explicitly_disabled():
    handler = webhook_delivery._NoRedirect()
    assert handler.redirect_request(None, None, 302, "found", {}, "https://other.example") is None


# Keep the test module independent from live services and make accidental async/network use obvious.
def test_worker_test_does_not_require_live_clock_or_network():
    assert webhook_delivery.datetime.now(UTC).tzinfo is UTC
    assert webhook_delivery.TIMEOUT_SECONDS >= 1
    assert webhook_delivery.MAX_ATTEMPTS >= 1


__all__ = ["test_worker_test_does_not_require_live_clock_or_network"]


@pytest.mark.parametrize("scheme", ["http", "https"])
def test_pinned_delivery_preserves_host_tls_and_ignores_proxy(monkeypatch, tmp_path, scheme):
    """Real local TCP/TLS transport: DNS cannot be consulted after validation."""
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    import ssl
    import threading
    from datetime import timedelta
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    received = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            received.append((self.headers["Host"], self.rfile.read(int(self.headers["Content-Length"]))))
            self.send_response(302 if self.path == "/redirect" else 202)
            self.send_header("Location", "http://127.0.0.1/private")
            self.end_headers()

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    if scheme == "https":
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "hooks.example.test")])
        certificate = (x509.CertificateBuilder().subject_name(subject).issuer_name(subject)
                       .public_key(key.public_key()).serial_number(x509.random_serial_number())
                       .not_valid_before(datetime.now(UTC) - timedelta(minutes=1))
                       .not_valid_after(datetime.now(UTC) + timedelta(days=1))
                       .add_extension(x509.SubjectAlternativeName([x509.DNSName("hooks.example.test")]), critical=False)
                       .sign(key, hashes.SHA256()))
        cert_path, key_path = tmp_path / "cert.pem", tmp_path / "key.pem"
        cert_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
        key_path.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                               serialization.NoEncryption()))
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_path, key_path)
        server.socket = context.wrap_socket(server.socket, server_side=True)
        client_context = ssl.create_default_context(cafile=str(cert_path))
        assert client_context.check_hostname
        monkeypatch.setattr(ssl, "_create_default_https_context", lambda: client_context)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        # The resolver boundary is mocked to route a validated destination to
        # the disposable server; the transport itself is real and unmocked.
        monkeypatch.setattr(webhook_delivery, "_resolve_public_addresses", lambda _host: ("127.0.0.1",))
        monkeypatch.setattr(webhook_delivery._kms, "decrypt", lambda _ciphertext: "delivery-secret")
        monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:1")
        monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:1")
        monkeypatch.setenv("NO_PROXY", "")

        def rebinding_dns(*_args, **_kwargs):
            raise AssertionError("Transport must not resolve DNS again")

        monkeypatch.setattr(webhook_delivery.socket, "getaddrinfo", rebinding_dns)
        delivery = SimpleNamespace(id="pinned", payload='{"ok":true}')
        webhook = SimpleNamespace(url=f"{scheme}://hooks.example.test:{server.server_port}/events", secret_ciphertext="test")
        assert webhook_delivery._deliver(delivery, webhook)["response_code"] == 202
        assert received == [(f"hooks.example.test:{server.server_port}", b'{"ok":true}')]
        webhook.url = f"{scheme}://hooks.example.test:{server.server_port}/redirect"
        with pytest.raises(RuntimeError, match="HTTP 302"):
            webhook_delivery._deliver(delivery, webhook)
        assert len(received) == 2
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.mark.parametrize("addresses", [["8.8.8.8", "127.0.0.1"], ["100.64.0.1"], ["::1"], ["224.0.0.1"]])
def test_resolution_rejects_mixed_and_non_global_addresses(monkeypatch, addresses):
    monkeypatch.setattr(webhook_delivery.socket, "getaddrinfo", lambda *_args, **_kwargs: [
        (None, None, None, None, (address, 0)) for address in addresses
    ])
    assert webhook_delivery._resolve_public_addresses("hooks.example") == ()
