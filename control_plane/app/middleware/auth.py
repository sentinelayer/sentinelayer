from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.resource_patterns = {
            "admin": ["/api/v1/tenants", "/api/v1/applications"],
            "user": ["/api/v1/metrics", "/api/v1/auth"],
        }

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path.startswith("/api/v1/admin"):
            token = request.headers.get("Authorization")
            if not token:
                return JSONResponse(status_code=401, content={"error": "Unauthorized"})
        return await call_next(request)
