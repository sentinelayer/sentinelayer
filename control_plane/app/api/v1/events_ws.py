from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime


import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from control_plane.app.runtime import is_production
from control_plane.app.infrastructure.db.models import AuthSession, User, RuntimeEvent, TenantEventOffset
from control_plane.app.api.v1.events import _serialize
from sqlalchemy.exc import SQLAlchemyError
from control_plane.app.infrastructure.db.session import AuthSessionLocal, SessionLocal, set_tenant_context

router = APIRouter(prefix="/events-ws", tags=["events"])
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
SESSION_RECHECK_SECONDS = 30
EVENT_POLL_SECONDS = 1
SEND_TIMEOUT_SECONDS = 5


def _claims(websocket: WebSocket) -> tuple[str, str] | None:
    if not JWT_SECRET:
        return None
    authorization = websocket.headers.get("authorization")
    token = authorization.removeprefix("Bearer ").strip() if authorization else websocket.query_params.get("token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM], options={"require": ["exp", "sub", "tenant_id"] + (["jti"] if is_production() else [])})
    except jwt.PyJWTError:
        return None
    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    if not user_id or not tenant_id:
        return None
    if token_id := payload.get("jti"):
        session_factory = getattr(websocket.app.state, "auth_session_factory", getattr(websocket.app.state, "session_factory", AuthSessionLocal))
        db = session_factory()
        try:
            session = db.query(AuthSession).filter(
                AuthSession.token_id == token_id,
                AuthSession.user_id == user_id,
                AuthSession.tenant_id == tenant_id,
                AuthSession.revoked_at.is_(None),
                AuthSession.expires_at > datetime.now(UTC),
            ).first()
            user = db.query(User).filter(
                User.id == user_id, User.tenant_id == tenant_id,
                User.is_active.is_(True),
            ).first()
            if not session or not user:
                return None
        finally:
            db.close()
    return str(user_id), str(tenant_id)


def _read_events(websocket, tenant, after):
    factory = getattr(websocket.app.state, "session_factory", SessionLocal)
    with factory() as db:
        set_tenant_context(db, tenant)
        offset = db.get(TenantEventOffset, tenant)
        latest = offset.last_sequence if offset else 0
        if after is None:
            return latest, []
        rows = db.query(RuntimeEvent).filter(RuntimeEvent.tenant_id == tenant,
                                             RuntimeEvent.sequence > after).order_by(
                                                 RuntimeEvent.sequence.asc()).limit(100).all()
        return latest, [_serialize(row) for row in rows]


@router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    try:
        claims = await asyncio.to_thread(_claims, websocket)
        if not claims:
            await websocket.close(code=1008, reason="Valid bearer token required")
            return
        _, tenant = claims
        raw = websocket.query_params.get("after")
        if raw is not None and (not raw.isascii() or not raw.isdecimal() or len(raw) > 19
                                or int(raw) > 9223372036854775807):
            await websocket.close(code=1008, reason="Invalid event cursor")
            return
        after = int(raw) if raw is not None else None
        latest, _ = await asyncio.to_thread(_read_events, websocket, tenant, None)
        if after is not None and after > latest:
            await websocket.close(code=1008, reason="Event cursor is ahead of this tenant")
            return
        cursor = latest if after is None else after
        await websocket.accept()
        await asyncio.wait_for(websocket.send_json({"type": "stream.ready", "cursor": cursor,
                                                    "latest": latest}), timeout=SEND_TIMEOUT_SECONDS)
        while True:
            if await asyncio.to_thread(_claims, websocket) != claims:
                await websocket.close(code=1008, reason="Session revoked or expired")
                return
            _, events = await asyncio.to_thread(_read_events, websocket, tenant, cursor)
            for event in events:
                if await asyncio.to_thread(_claims, websocket) != claims:
                    await websocket.close(code=1008, reason="Session revoked or expired")
                    return
                await asyncio.wait_for(websocket.send_json({"type": "event", "cursor": event["sequence"],
                                                            "event": event}), timeout=SEND_TIMEOUT_SECONDS)
                cursor = event["sequence"]
            if len(events) == 100:
                continue
            try:
                message = await asyncio.wait_for(websocket.receive_text(),
                    timeout=min(EVENT_POLL_SECONDS, SESSION_RECHECK_SECONDS))
            except asyncio.TimeoutError:
                continue
            if await asyncio.to_thread(_claims, websocket) != claims:
                await websocket.close(code=1008, reason="Session revoked or expired")
                return
            if message != "ping":
                await websocket.close(code=1008, reason="Event stream accepts ping only")
                return
            await asyncio.wait_for(websocket.send_json({"type": "pong", "cursor": cursor}),
                                   timeout=SEND_TIMEOUT_SECONDS)
    except WebSocketDisconnect:
        pass
    except (SQLAlchemyError, asyncio.TimeoutError):
        await websocket.close(code=1013, reason="Event stream temporarily unavailable; reconnect with cursor")
