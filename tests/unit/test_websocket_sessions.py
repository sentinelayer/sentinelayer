from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import jwt
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
        db.add(User(id="u", email="u@example.com", hashed_password="fixture", tenant_id="t", is_active=True))
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
