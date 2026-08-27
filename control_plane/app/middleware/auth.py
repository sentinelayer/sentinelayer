from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime

import jwt
from fastapi import Request
from sqlalchemy import or_
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from control_plane.app.infrastructure.db.models import ApiKeyRecord
from control_plane.app.infrastructure.db.session import SessionLocal

PUBLIC_PATHS = {
    "/",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/health",
    "/health/readiness",
    "/metrics",
    "/api/v1/health",
    "/api/v1/health/readiness",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/openapi"):
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")
        if api_key:
            secret = api_key.strip()
            if len(secret) < 24:
                return JSONResponse(status_code=401, content={"error": "Invalid API key"})
            db = SessionLocal()
            try:
                digest = hashlib.sha256(secret.encode("utf-8")).hexdigest()
                now = datetime.now(UTC)
                row = db.query(ApiKeyRecord).filter(
                    ApiKeyRecord.key_hash == digest,
                    ApiKeyRecord.revoked_at.is_(None),
                    or_(ApiKeyRecord.expires_at.is_(None), ApiKeyRecord.expires_at > now),
                ).first()
                if not row:
                    return JSONResponse(status_code=401, content={"error": "Invalid or expired API key"})
                row.last_used_at = now
                db.commit()
                request.state.user_id = row.user_id
                request.state.tenant_id = row.tenant_id
                request.state.is_admin = False
                request.state.roles = []
                request.state.auth_method = "api_key"
            finally:
                db.close()
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"error": "Missing or invalid token"})

        parts = auth_header.split(" ", 1)
        if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
            return JSONResponse(status_code=401, content={"error": "Missing or invalid token"})
        token = parts[1].strip()
        secret = os.environ.get("JWT_SECRET")
        if not secret:
            return JSONResponse(status_code=500, content={"error": "JWT_SECRET not configured"})
        try:
            payload = jwt.decode(token, secret, algorithms=["HS256"])
            request.state.user_id = payload.get("sub")
            request.state.tenant_id = payload.get("tenant_id")
            request.state.is_admin = bool(payload.get("is_admin", False))
            request.state.roles = payload.get("roles", []) or []
            request.state.auth_method = "jwt"
            if not request.state.user_id or not request.state.tenant_id:
                return JSONResponse(status_code=401, content={"error": "Invalid token claims"})
        except jwt.ExpiredSignatureError:
            return JSONResponse(status_code=401, content={"error": "Token expired"})
        except jwt.InvalidTokenError:
            return JSONResponse(status_code=401, content={"error": "Invalid token"})

        return await call_next(request)
