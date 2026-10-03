"""A silent TCP peer must not hold an engine thread indefinitely."""
import socket
import threading
import time
import pytest
from fastapi import HTTPException
from engine.behavior.server import SharedBehaviorState, BehaviorRequest
from engine.risk.correlation import RiskCorrelation, CorrelationUnavailable


def test_silent_redis_peer_has_bounded_failure(monkeypatch):
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen()
    server.settimeout(.1)
    peers = []
    stop = threading.Event()
    def accept():
        while not stop.is_set():
            try: peers.append(server.accept()[0])
            except socket.timeout: pass
            except OSError: return
    thread = threading.Thread(target=accept, daemon=True)
    thread.start()
    url = f"redis://127.0.0.1:{server.getsockname()[1]}/0"
    monkeypatch.setenv("REDIS_URL", url)
    state = SharedBehaviorState()
    risk = RiskCorrelation(redis_url=url)
    try:
        started = time.monotonic()
        with pytest.raises(HTTPException) as failure:
            state.analyze(BehaviorRequest(endpoint="/safe", client_id="silent-peer-test"))
        assert failure.value.status_code == 503
        assert time.monotonic() - started < 1
        started = time.monotonic()
        with pytest.raises(CorrelationUnavailable):
            risk.add_signal("silent-peer-test", "waf_block", {})
        assert time.monotonic() - started < 1
    finally:
        stop.set()
        server.close()
        thread.join(timeout=1)
        for peer in peers: peer.close()
        state.redis_client.close()
        risk._redis.close()
