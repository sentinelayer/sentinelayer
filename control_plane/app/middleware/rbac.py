from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RBACMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.resource_patterns = {
            "admin": ["/api/v1/tenants", "/api/v1/applications", "/api/v1/policies"],
            "user": ["/api/v1/metrics", "/api/v1/health"],
        }

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        for pattern in self.resource_patterns.get("admin", []):
            if path.startswith(pattern):
                roles = getattr(request.state, "roles", [])
                if "admin" not in roles:
                    return JSONResponse(status_code=403, content={"error": "Admin access required"})
        return await call_next(request)
