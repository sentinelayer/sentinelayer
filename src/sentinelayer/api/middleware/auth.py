from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

from sentinelayer.backend.internal.auth.jwt_handler import verify_token, TokenPayload

logger = logging.getLogger(__name__)

class AuthMiddleware:
    """Authentication middleware untuk FastAPI"""
    
    def __init__(self):
        self.security = HTTPBearer(auto_error=False)
    
    async def __call__(self, request: Request) -> Optional[TokenPayload]:
        """Validate JWT token from Authorization header"""
        
        # Skip auth for public endpoints
        public_paths = ["/health", "/docs", "/redoc", "/openapi.json", "/", "/api/v1/auth/login"]
        if request.url.path in public_paths:
            return None
        
        # Get token
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authorization header"
            )
        
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authorization scheme"
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format"
            )
        
        # Verify token
        payload = verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        # Store user context in request state
        request.state.user = payload
        request.state.tenant_id = payload.tenant_id
        request.state.user_id = payload.sub
        
        logger.info(f"Authenticated: user={payload.sub}, tenant={payload.tenant_id}")
        return payload

# Dependency untuk FastAPI
async def get_current_user(request: Request) -> TokenPayload:
    """Dependency untuk mendapatkan current user"""
    auth_middleware = AuthMiddleware()
    user = await auth_middleware(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return user

async def get_current_tenant(request: Request) -> str:
    """Dependency untuk mendapatkan current tenant"""
    user = await get_current_user(request)
    return user.tenant_id
