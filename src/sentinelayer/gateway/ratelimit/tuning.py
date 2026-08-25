from typing import Dict, Any, Optional

class RateLimitTuning:
    def __init__(self):
        self.endpoint_limits = {
            "GET /health": 1000,
            "POST /api/v1/auth/login": 5,
            "GET /api/v1/orders": 100,
            "POST /api/v1/orders": 50,
            "PUT /api/v1/orders": 30,
            "DELETE /api/v1/orders": 20,
            "GET /api/v1/orders/{order_id}": 100,
            "GET /api/v1/risk": 20,
            "POST /api/v1/risk": 10,
        }
        
        self.distributed_attack_threshold = 100
        self.window_seconds = 60
    
    def get_limit(self, endpoint: str, method: str) -> int:
        key = f"{method} {endpoint}"
        return self.endpoint_limits.get(key, 100)
    
    def set_limit(self, endpoint: str, method: str, limit: int) -> None:
        self.endpoint_limits[f"{method} {endpoint}"] = limit
    
    def get_limits(self) -> Dict[str, int]:
        return self.endpoint_limits
    
    def get_distributed_threshold(self) -> int:
        return self.distributed_attack_threshold

_tuning = None

def get_rate_limit_tuning():
    global _tuning
    if _tuning is None:
        _tuning = RateLimitTuning()
    return _tuning
