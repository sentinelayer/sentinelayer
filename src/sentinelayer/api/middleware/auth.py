from fastapi import Request, HTTPException, status
from typing import Optional
from sentinelayer.backend.internal.auth.jwt_handler import verify_token

class AuthMiddleware:
    async def __call__(self, request: Request) -> Optional[dict]:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Missing auth header")
        
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise HTTPException(status_code=401, detail="Invalid scheme")
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid header format")
        
        payload = verify_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        request.state.user = payload
        request.state.tenant_id = payload.tenant_id
        request.state.user_id = payload.sub
        return payload
