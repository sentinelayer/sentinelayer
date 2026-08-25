from fastapi import Request, HTTPException, status
from typing import Optional
from sentinelayer.backend.internal.auth.jwt_handler import verify_token

class AuthMiddleware:
    async def __call__(self, request: Request) -> Optional[dict]:
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
        
        print(f"Verifying token: {token[:20]}...")
        payload = verify_token(token)
        if not payload:
            print("Token verification failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        print(f"Token verified for user: {payload.sub}")
        request.state.user = payload.model_dump()
        request.state.tenant_id = payload.tenant_id
        request.state.user_id = payload.sub
        
        return request.state.user
