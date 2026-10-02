from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime
from collections import defaultdict

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from control_plane.app.runtime import is_production
from control_plane.app.infrastructure.db.models import AuthSession, User
from control_plane.app.infrastructure.db.session import AuthSessionLocal

router = APIRouter(prefix="/events-ws", tags=["events"])
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
SESSION_RECHECK_SECONDS = 30


class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, websocket: WebSocket, tenant_id: str) -> None:
        await websocket.accept()
        self.connections[tenant_id].add(websocket)

    def disconnect(self, websocket: WebSocket, tenant_id: str) -> None:
        connections = self.connections.get(tenant_id)
        if not connections:
            return
        connections.discard(websocket)
        if not connections:
            self.connections.pop(tenant_id, None)

    async def broadcast(self, message: str, tenant_id: str) -> None:
        stale: list[WebSocket] = []
        for connection in self.connections.get(tenant_id, set()).copy():
            try:
                claims = _claims(connection)
                if not claims or claims[1] != tenant_id:
                    await connection.close(code=1008, reason="Session revoked or expired")
                    stale.append(connection)
                    continue
                await connection.send_text(message)
            except Exception:  # noqa: BLE001 - remove dead sockets without breaking other subscribers
                stale.append(connection)
        for connection in stale:
            self.disconnect(connection, tenant_id)


manager = ConnectionManager()


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


@router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    claims = _claims(websocket)
    if not claims:
        await websocket.close(code=1008, reason="Valid bearer token required")
        return
    _, tenant_id = claims
    await manager.connect(websocket, tenant_id)
    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=SESSION_RECHECK_SECONDS)
            except asyncio.TimeoutError:
                if _claims(websocket) != claims:
                    await websocket.close(code=1008, reason="Session revoked or expired")
                    return
                continue
            if _claims(websocket) != claims:
                await websocket.close(code=1008, reason="Session revoked or expired")
                return
            await manager.broadcast(data, tenant_id)
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, tenant_id)
