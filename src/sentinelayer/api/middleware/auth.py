import os
import jwt
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        public_paths = ["/", "/docs", "/openapi.json", "/health", "/health/readiness", "/api/v1/auth/login", "/api/v1/auth/register"]
        if request.url.path in public_paths:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"error": "Missing or invalid token"})

        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, os.environ["JWT_SECRET"], algorithms=["HS256"])
            request.state.user_id = payload.get("sub")
            request.state.tenant_id = payload.get("tenant_id")
            request.state.is_admin = payload.get("is_admin", False)
            request.state.roles = payload.get("roles", [])
        except jwt.ExpiredSignatureError:
            return JSONResponse(status_code=401, content={"error": "Token expired"})
        except jwt.InvalidTokenError:
            return JSONResponse(status_code=401, content={"error": "Invalid token"})

        path = request.url.path
        if path.startswith("/api/v1/controlplane/tenants"):
            if not request.state.is_admin:
                return JSONResponse(status_code=403, content={"error": "Admin access required"})

        return await call_next(request)
