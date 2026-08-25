from fastapi import Request, HTTPException, status
from typing import Optional
from sentinelayer.backend.internal.auth.jwt_handler import verify_token, TokenPayload
import logging

logger = logging.getLogger(__name__)

class AuthMiddleware:
    """Authentication middleware using JWT"""
    
    async def __call__(self, request: Request) -> Optional[TokenPayload]:
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
                    detail="Invalid scheme"
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid header format"
            )
        
        payload = verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        # Store user context
        request.state.user = payload
        request.state.tenant_id = payload.tenant_id
        request.state.user_id = payload.sub
        
        logger.info(f"Authenticated: user={payload.sub}, tenant={payload.tenant_id}")
        return payload
