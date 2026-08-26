from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        public_paths = ["/", "/docs", "/openapi.json", "/health", "/health/readiness", "/api/v1/auth/login", "/api/v1/auth/register"]
        if request.url.path in public_paths:
            return await call_next(request)

        jwt_tenant = getattr(request.state, "tenant_id", None)
        header_tenant = request.headers.get("X-Tenant-ID")

        if jwt_tenant and header_tenant and jwt_tenant != header_tenant:
            return JSONResponse(
                status_code=403,
                content={"error": "Tenant mismatch: JWT tenant does not match header"}
            )

        if jwt_tenant:
            request.state.tenant_id = jwt_tenant
        elif header_tenant:
            request.state.tenant_id = header_tenant
        else:
            return JSONResponse(
                status_code=400,
                content={"error": "Missing tenant ID"}
            )

        return await call_next(request)
