from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time
from collections import defaultdict

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, calls_per_minute: int = 60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.requests = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        if request.url.path in ["/", "/docs", "/openapi.json", "/health", "/health/readiness"]:
            return await call_next(request)
        
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - 60
        
        self.requests[client_ip] = [t for t in self.requests[client_ip] if t > window_start]
        
        if len(self.requests[client_ip]) >= self.calls_per_minute:
            return JSONResponse(status_code=429, content={"error": "Rate limit exceeded"})
        
        self.requests[client_ip].append(now)
        return await call_next(request)
