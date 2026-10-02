from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import jwt
import secrets
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from control_plane.app.api.v1 import events_ws
from control_plane.app.infrastructure.db.models import Base, User, AuthSession


def test_websocket_rejects_revoked_and_expired_sessions(monkeypatch):
    monkeypatch.setenv("SL_ENV", "test")
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    secret = "test-only-websocket-secret-32-characters"
    monkeypatch.setattr(events_ws, "JWT_SECRET", secret)
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    now = datetime.now(UTC)
    with sessions() as db:
        db.add(User(id="u", email="u@example.com", hashed_password=secrets.token_hex(32), tenant_id="t", is_active=True))
        db.add(AuthSession(token_id="j", user_id="u", tenant_id="t", created_at=now, expires_at=now + timedelta(minutes=5)))
        db.commit()
    value = jwt.encode({"sub": "u", "tenant_id": "t", "jti": "j", "exp": now + timedelta(minutes=5)}, secret, algorithm="HS256")
    socket = SimpleNamespace(headers={"authorization": f"Bearer {value}"}, query_params={},
                             app=SimpleNamespace(state=SimpleNamespace(session_factory=sessions)))
    try:
        assert events_ws._claims(socket) == ("u", "t")
        with sessions() as db:
            db.query(AuthSession).first().revoked_at = now
            db.commit()
        assert events_ws._claims(socket) is None
        with sessions() as db:
            row = db.query(AuthSession).first()
            row.revoked_at = None
            row.expires_at = now - timedelta(minutes=1)
            db.commit()
        assert events_ws._claims(socket) is None
    finally:
        engine.dispose()


import pytest


@pytest.mark.parametrize("trigger", ["idle", "broadcast"])
def test_revoked_listener_closes_without_sending_messages(monkeypatch, trigger):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy.pool import StaticPool
    from starlette.websockets import WebSocketDisconnect

    secret = "test-only-websocket-secret-32-characters"
    monkeypatch.setattr(events_ws, "JWT_SECRET", secret)
    monkeypatch.setattr(events_ws, "SESSION_RECHECK_SECONDS", 0.02 if trigger == "idle" else 30)
    manager = events_ws.ConnectionManager()
    monkeypatch.setattr(events_ws, "manager", manager)
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    now = datetime.now(UTC)
    with sessions() as db:
        db.add(User(id="u", email="u@example.com", hashed_password=secrets.token_hex(32), tenant_id="t", is_active=True))
        for identity in ("listener", "sender"):
            db.add(AuthSession(token_id=identity, user_id="u", tenant_id="t", created_at=now,
                               expires_at=now + timedelta(minutes=5)))
        db.commit()
    app = FastAPI()
    app.include_router(events_ws.router, prefix="/api/v1")
    app.state.session_factory = sessions

    def url(identity):
        value = jwt.encode({"sub": "u", "tenant_id": "t", "jti": identity,
                            "exp": now + timedelta(minutes=5)}, secret, algorithm="HS256")
        return f"/api/v1/events-ws/stream?token={value}"

    try:
        with TestClient(app) as client:
            with client.websocket_connect(url("listener")) as listener:
                with client.websocket_connect(url("sender")) as sender:
                    with sessions() as db:
                        db.query(AuthSession).filter(AuthSession.token_id == "listener").first().revoked_at = now
                        db.commit()
                    if trigger == "broadcast":
                        sender.send_text("sensitive-event")
                        assert sender.receive_text() == "sensitive-event"
                    with pytest.raises(WebSocketDisconnect) as closed:
                        listener.receive_text()
                    assert closed.value.code == 1008
        assert manager.connections == {}
    finally:
        engine.dispose()
