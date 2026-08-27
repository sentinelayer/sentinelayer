from __future__ import annotations

import os
from collections import defaultdict

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(prefix="/events-ws", tags=["events"])
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"


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
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    return (str(user_id), str(tenant_id)) if user_id and tenant_id else None


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
            data = await websocket.receive_text()
            await manager.broadcast(data, tenant_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, tenant_id)
