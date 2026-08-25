from fastapi import Request, HTTPException, status
import logging
from sentinelayer.backend.internal.auth.authorization import AuthorizationMiddleware

logger = logging.getLogger(__name__)

class TenantMiddleware:
    """Tenant isolation middleware"""
    
    def __init__(self):
        self.auth = AuthorizationMiddleware()
    
    async def __call__(self, request: Request):
        """Validate tenant isolation untuk setiap request"""
        
        # Skip for public endpoints
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json", "/"]:
            return
        
        # Get tenant from request state (set by auth middleware)
        tenant_id = getattr(request.state, "tenant_id", None)
        user_id = getattr(request.state, "user_id", None)
        
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tenant context not found"
            )
        
        # Extract resource from path (BOLA check)
        resource = self.auth.extract_resource_from_path(request.url.path)
        if resource:
            resource_type, resource_id = resource
            # For now, just log the BOLA attempt
            # Actual BOLA check should query database
            logger.info(f"BOLA check: {resource_type} {resource_id} by user {user_id} in tenant {tenant_id}")
        
        # Add tenant context to request
        request.state.tenant = tenant_id
        logger.info(f"Tenant context: {tenant_id} for user {user_id}")
