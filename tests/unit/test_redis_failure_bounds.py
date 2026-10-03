"""A silent TCP peer must not hold an engine thread indefinitely."""
import socket
import asyncio
import threading
import time
import pytest
from fastapi import HTTPException
from engine.behavior.server import SharedBehaviorState, BehaviorRequest
from engine.risk.correlation import RiskCorrelation, CorrelationUnavailable


@pytest.mark.parametrize("asynchronous", [False, True])
def test_silent_redis_peer_has_bounded_failure(monkeypatch, asynchronous):
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
            request = BehaviorRequest(endpoint="/safe", client_id="silent-peer-test")
            if asynchronous:
                asyncio.run(state.analyze_async(request))
            else:
                state.analyze(request)
        assert failure.value.status_code == 503
        assert time.monotonic() - started < 1
        started = time.monotonic()
        with pytest.raises(CorrelationUnavailable):
            if asynchronous:
                asyncio.run(risk.observe_async("silent-peer-test", ["waf_block"], {}))
            else:
                risk.add_signal("silent-peer-test", "waf_block", {})
        assert time.monotonic() - started < 1
    finally:
        stop.set()
        server.close()
        thread.join(timeout=1)
        for peer in peers: peer.close()
        asyncio.run(state.close_async())
        asyncio.run(risk.close_async())
        state.redis_client.close()
        risk._redis.close()
