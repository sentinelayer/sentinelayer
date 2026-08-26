from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in ["/", "/docs", "/openapi.json", "/health", "/health/readiness", "/api/v1/auth/login", "/api/v1/auth/register"]:
            return await call_next(request)
        
        tenant_id = request.headers.get("X-Tenant-ID")
        if not tenant_id:
            tenant_id = request.state.tenant_id if hasattr(request.state, "tenant_id") else None
        
        if not tenant_id:
            return JSONResponse(status_code=400, content={"error": "Missing tenant ID"})
        
        request.state.tenant_id = tenant_id
        return await call_next(request)
