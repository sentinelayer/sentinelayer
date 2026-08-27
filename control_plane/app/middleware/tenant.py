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
    "/api/v1/health",
    "/api/v1/health/readiness",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
}


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/openapi"):
            return await call_next(request)
        # Frontend documents and assets are same-origin and do not carry tenant
        # context; tenant enforcement applies to the API surface only.
        if not path.startswith("/api/"):
            return await call_next(request)

        jwt_tenant = getattr(request.state, "tenant_id", None)
        header_tenant = request.headers.get("X-Tenant-ID")

        if jwt_tenant and header_tenant and jwt_tenant != header_tenant:
            return JSONResponse(
                status_code=403,
                content={"error": "Tenant mismatch: JWT tenant does not match header"},
            )

        if jwt_tenant:
            request.state.tenant_id = jwt_tenant
        elif header_tenant:
            request.state.tenant_id = header_tenant
        else:
            return JSONResponse(status_code=400, content={"error": "Missing tenant ID"})

        return await call_next(request)
