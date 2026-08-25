from fastapi import Request, HTTPException, status
from typing import Optional

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

        if token == "valid-token-for-testing-12345":
            request.state.user = {
                "sub": "user-123",
                "tenant_id": "tenant-acme",
                "email": "test@example.com",
                "roles": ["user", "admin"]
            }
            request.state.tenant_id = "tenant-acme"
            request.state.user_id = "user-123"
            return request.state.user

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
