import time
import hashlib
from typing import Dict

class SimpleRateLimiter:
    """Rate limiter tanpa Redis (buat testing dulu)"""
    
    def __init__(self):
        self.requests = {}  # key -> list of timestamps
    
    def is_allowed(self, dimension: str, identifier: str, endpoint: str = "", limit: int = 100, window: int = 60) -> Dict:
        key = f"{dimension}:{identifier}:{endpoint}"
        now = time.time()
        
        # Clean old requests
        if key in self.requests:
            self.requests[key] = [t for t in self.requests[key] if t > now - window]
        else:
            self.requests[key] = []
        
        # Check limit
        if len(self.requests[key]) >= limit:
            return {
                "allowed": False,
                "remaining": 0,
                "reset_in": int(window),
                "limit": limit,
                "window": window,
                "dimension": dimension
            }
        
        # Add request
        self.requests[key].append(now)
        
        return {
            "allowed": True,
            "remaining": limit - len(self.requests[key]) - 1,
            "reset_in": int(window),
            "limit": limit,
            "window": window,
            "dimension": dimension
        }