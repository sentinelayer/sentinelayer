from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RBACMiddleware(BaseHTTPMiddleware):
    """Deny privileged resource paths unless the validated JWT is admin."""

    ADMIN_PREFIXES = (
        "/api/v1/admin",
        "/api/v1/users",
        "/api/v1/configuration",
        "/api/v1/gates",
        "/api/v1/evidence",
        "/api/v1/offboarding",
        "/api/v1/webhooks",
    )

    async def dispatch(self, request: Request, call_next):
        path = request.url.path.rstrip("/") or "/"
        if any(path == prefix or path.startswith(prefix + "/") for prefix in self.ADMIN_PREFIXES):
            is_admin = bool(getattr(request.state, "is_admin", False))
            roles = getattr(request.state, "roles", []) or []
            if not is_admin and "admin" not in roles:
                return JSONResponse(status_code=403, content={"error": "Admin access required"})
        return await call_next(request)
