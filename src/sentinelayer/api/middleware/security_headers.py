from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self' https:; "
            "script-src 'self' 'unsafe-inline' https:; "
            "style-src 'self' 'unsafe-inline' https:; "
            "img-src 'self' data: https:; "
            "font-src 'self' https:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'self'; "
            "form-action 'self'; "
            "base-uri 'self';"
        )
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Server"] = "SentinelLayer"
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        return response
