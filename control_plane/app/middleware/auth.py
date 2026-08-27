import os

import jwt
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

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
            if not request.state.user_id or not request.state.tenant_id:
                return JSONResponse(status_code=401, content={"error": "Invalid token claims"})
        except jwt.ExpiredSignatureError:
            return JSONResponse(status_code=401, content={"error": "Token expired"})
        except jwt.InvalidTokenError:
            return JSONResponse(status_code=401, content={"error": "Invalid token"})

        return await call_next(request)
