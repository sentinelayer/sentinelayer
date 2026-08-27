from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class MFAGateMiddleware(BaseHTTPMiddleware):
    """Require a recently MFA-verified JWT for privileged control-plane mutations."""

    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

    @classmethod
    def requires_mfa(cls, request: Request) -> bool:
        path = request.url.path.rstrip("/") or "/"
        if path.startswith("/api/v1/admin"):
            return True
        if request.method.upper() in cls.SAFE_METHODS:
            return False
        return path == "/api/v1/policies" or path.startswith("/api/v1/policies/") or path == "/api/v1/risk/calibrations" or path.startswith("/api/v1/risk/calibrations/")

    async def dispatch(self, request: Request, call_next):
        if self.requires_mfa(request) and not getattr(request.state, "mfa_verified", False):
            return JSONResponse(
                status_code=401,
                content={"error": "MFA required", "code": "MFA_REQUIRED"},
                headers={"WWW-Authenticate": "Bearer error=\"mfa_required\""},
            )
        return await call_next(request)
