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
    MUTATING_TENANT_PREFIXES = (
        "/api/v1/policies",
        "/api/v1/risk/calibrations",
    )
    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

    @classmethod
    def requires_admin(cls, request: Request) -> bool:
        path = request.url.path.rstrip("/") or "/"
        if any(path == prefix or path.startswith(prefix + "/") for prefix in cls.ADMIN_PREFIXES):
            return True
        return (
            request.method.upper() not in cls.SAFE_METHODS
            and any(path == prefix or path.startswith(prefix + "/") for prefix in cls.MUTATING_TENANT_PREFIXES)
        )

    async def dispatch(self, request: Request, call_next):
        if self.requires_admin(request):
            is_admin = bool(getattr(request.state, "is_admin", False))
            roles = getattr(request.state, "roles", []) or []
            if not is_admin and "admin" not in roles:
                return JSONResponse(status_code=403, content={"error": "Admin access required"})
        return await call_next(request)
