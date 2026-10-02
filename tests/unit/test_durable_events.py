import json
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.websockets import WebSocketDisconnect

from control_plane.app.api.v1 import events_ws
from control_plane.app.domain.events import append_event
from control_plane.app.infrastructure.db.models import Base, RuntimeEvent, TenantEventOffset


def test_event_and_cursor_roll_back_together(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'events.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    try:
        with factory() as db:
            append_event(db, "tenant-a", "test.failed")
            db.rollback()
            assert db.query(RuntimeEvent).count() == 0
            assert db.get(TenantEventOffset, "tenant-a") is None
            event = append_event(db, "tenant-a", "test.success")
            assert event.sequence == 1
            db.commit()
        with factory() as db:
            assert append_event(db, "tenant-a", "test.next").sequence == 2
            assert append_event(db, "tenant-b", "test.other").sequence == 1
            db.commit()
    finally:
        engine.dispose()


def test_independent_workers_replay_committed_events_and_reject_client_injection(monkeypatch, tmp_path):
    secret = "durable-event-test-secret-32-characters"
    monkeypatch.setattr(events_ws, "JWT_SECRET", secret)
    monkeypatch.setattr(events_ws, "EVENT_POLL_SECONDS", .02)
    monkeypatch.setenv("SL_ENV", "test")
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    engines = [create_engine(f"sqlite:///{tmp_path / 'shared.db'}") for _ in range(2)]
    Base.metadata.create_all(engines[0])
    factories = [sessionmaker(bind=engine) for engine in engines]
    apps = []
    for factory in factories:
        app = FastAPI()
        app.state.session_factory = factory
        app.include_router(events_ws.router, prefix="/api/v1")
        apps.append(app)
    token = jwt.encode({"sub": "reader", "tenant_id": "tenant-a", "exp": datetime.now(UTC) + timedelta(minutes=5)}, secret, algorithm="HS256")
    url = f"/api/v1/events-ws/stream?token={token}&after=0"
    try:
        with TestClient(apps[0]) as worker_a, TestClient(apps[1]) as worker_b:
            with worker_b.websocket_connect(url) as listener:
                assert listener.receive_json()["type"] == "stream.ready"
                with factories[0]() as db:
                    append_event(db, "tenant-b", "test.secret", data={"secret": "other tenant"})
                    own = append_event(db, "tenant-a", "test.delivery", data={"value": "durable"})
                    own_id = own.id
                    db.commit()
                delivered = listener.receive_json()
                assert delivered["event"]["id"] == own_id
                assert delivered["cursor"] == 1
                assert "secret" not in json.dumps(delivered)
            # A new worker/connection replays the same persisted event.
            with worker_a.websocket_connect(url) as reconnect:
                reconnect.receive_json()
                assert reconnect.receive_json()["event"]["id"] == own_id
            with worker_a.websocket_connect(url.replace("after=0", "after=1")) as inject:
                inject.receive_json()
                inject.send_text("forged-server-event")
                with pytest.raises(WebSocketDisconnect) as closed:
                    inject.receive_json()
                assert closed.value.code == 1008
            with pytest.raises(WebSocketDisconnect):
                with worker_a.websocket_connect(url.replace("after=0", "after=999")):
                    pass
    finally:
        for engine in engines:
            engine.dispose()
