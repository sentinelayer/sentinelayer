from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Public paths
        if request.url.path in ["/", "/docs", "/openapi.json", "/health", "/health/readiness", "/api/v1/auth/login", "/api/v1/auth/register"]:
            return await call_next(request)
        
        # JWT tenant is authoritative
        jwt_tenant = getattr(request.state, "tenant_id", None)
        header_tenant = request.headers.get("X-Tenant-ID")
        
        # If JWT has tenant, it MUST match header if header provided
        if jwt_tenant and header_tenant and jwt_tenant != header_tenant:
            return JSONResponse(
                status_code=403,
                content={"error": "Tenant mismatch: JWT tenant does not match header"}
            )
        
        # Use JWT tenant as source of truth
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
