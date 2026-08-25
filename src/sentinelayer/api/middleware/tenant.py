from fastapi import Request, HTTPException, status

class TenantMiddleware:
    async def __call__(self, request: Request):
        tenant_id = getattr(request.state, "tenant_id", None)
        if not tenant_id:
            raise HTTPException(status_code=401, detail="Tenant context missing")
        return
