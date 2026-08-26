from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class RBACMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path.startswith("/api/v1/admin"):
            roles = getattr(request.state, "roles", [])
            if "admin" not in roles:
                return JSONResponse(status_code=403, content={"error": "Admin access required"})
        return await call_next(request)
