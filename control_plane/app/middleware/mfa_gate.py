from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class MFAGateMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path.startswith("/api/v1/admin") or path.startswith("/api/v1/policies"):
            mfa_verified = getattr(request.state, "mfa_verified", False)
            if not mfa_verified:
                return JSONResponse(status_code=401, content={"error": "MFA required"})
        return await call_next(request)
