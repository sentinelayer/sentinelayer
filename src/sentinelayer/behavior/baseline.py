import time
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import statistics

@dataclass
class BaselineProfile:
    """Baseline profile untuk endpoint/user/session"""
    endpoint: str
    method: str
    user_id: str
    tenant_id: str
    sample_count: int = 0
    avg_response_time: float = 0.0
    avg_request_size: float = 0.0
    avg_response_size: float = 0.0
    status_codes: Dict[int, int] = field(default_factory=dict)
    request_patterns: List[str] = field(default_factory=list)
    time_series: List[float] = field(default_factory=list)
    last_updated: float = field(default_factory=time.time)
    is_stable: bool = False
    min_samples_required: int = 100

    def update(self, request_data: Dict[str, Any]):
        """Update baseline dengan data request baru"""
        self.sample_count += 1
        
        # Response time
        rt = request_data.get("response_time", 0)
        self.avg_response_time = ((self.avg_response_time * (self.sample_count - 1)) + rt) / self.sample_count
        
        # Request size
        req_size = request_data.get("request_size", 0)
        self.avg_request_size = ((self.avg_request_size * (self.sample_count - 1)) + req_size) / self.sample_count
        
        # Response size
        resp_size = request_data.get("response_size", 0)
        self.avg_response_size = ((self.avg_response_size * (self.sample_count - 1)) + resp_size) / self.sample_count
        
        # Status codes
        status = request_data.get("status_code", 200)
        self.status_codes[status] = self.status_codes.get(status, 0) + 1
        
        # Time series (keep last 100)
        self.time_series.append(rt)
        if len(self.time_series) > 100:
            self.time_series.pop(0)
        
        # Check stability
        if self.sample_count >= self.min_samples_required and len(self.time_series) >= 30:
            self.is_stable = True
        
        self.last_updated = time.time()
    
    def get_anomaly_score(self, request_data: Dict[str, Any]) -> float:
        """Hitung anomaly score (0-1)"""
        if not self.is_stable or self.sample_count < self.min_samples_required:
            return 0.5  # Neutral jika belum stabil
        
        score = 0.0
        factors = 0
        
        # Response time anomaly
        rt = request_data.get("response_time", 0)
        if rt > 0 and self.avg_response_time > 0:
            rt_ratio = rt / self.avg_response_time
            if rt_ratio > 3.0:
                score += 0.3
                factors += 1
            elif rt_ratio > 2.0:
                score += 0.15
                factors += 1
        
        # Request size anomaly
        req_size = request_data.get("request_size", 0)
        if req_size > 0 and self.avg_request_size > 0:
            size_ratio = req_size / self.avg_request_size
            if size_ratio > 5.0:
                score += 0.2
                factors += 1
            elif size_ratio > 3.0:
                score += 0.1
                factors += 1
        
        # Status code anomaly
        status = request_data.get("status_code", 200)
        if status in [400, 401, 403, 404, 500]:
            score += 0.2
            factors += 1
        
        return min(1.0, score)

class BaselineManager:
    """Manages baseline profiles for all endpoints/users"""
    
    def __init__(self):
        self.profiles: Dict[str, BaselineProfile] = {}
        self.learning_mode = True
        self.learning_samples = 100
    
    def get_profile_key(self, endpoint: str, method: str, user_id: str, tenant_id: str) -> str:
        return f"{tenant_id}:{user_id}:{method}:{endpoint}"
    
    def record_request(self, request_data: Dict[str, Any]) -> BaselineProfile:
        """Record a request and update baseline"""
        key = self.get_profile_key(
            request_data.get("endpoint", ""),
            request_data.get("method", "GET"),
            request_data.get("user_id", "unknown"),
            request_data.get("tenant_id", "default")
        )
        
        if key not in self.profiles:
            self.profiles[key] = BaselineProfile(
                endpoint=request_data.get("endpoint", ""),
                method=request_data.get("method", "GET"),
                user_id=request_data.get("user_id", "unknown"),
                tenant_id=request_data.get("tenant_id", "default")
            )
        
        self.profiles[key].update(request_data)
        
        # Check if still in learning mode
        stable_count = sum(1 for p in self.profiles.values() if p.is_stable)
        if stable_count >= len(self.profiles) * 0.8:
            self.learning_mode = False
        
        return self.profiles[key]
    
    def detect_anomaly(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect if a request is anomalous"""
        key = self.get_profile_key(
            request_data.get("endpoint", ""),
            request_data.get("method", "GET"),
            request_data.get("user_id", "unknown"),
            request_data.get("tenant_id", "default")
        )
        
        if key not in self.profiles:
            return {
                "is_anomaly": False,
                "score": 0.5,
                "reason": "No baseline profile yet",
                "confidence": 0.2
            }
        
        profile = self.profiles[key]
        score = profile.get_anomaly_score(request_data)
        
        is_anomaly = score > 0.6 and not self.learning_mode
        
        return {
            "is_anomaly": is_anomaly,
            "score": score,
            "reason": "Anomaly detected" if is_anomaly else "Normal behavior",
            "confidence": min(1.0, profile.sample_count / 100),
            "sample_count": profile.sample_count,
            "is_stable": profile.is_stable
        }
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_profiles": len(self.profiles),
            "stable_profiles": sum(1 for p in self.profiles.values() if p.is_stable),
            "learning_mode": self.learning_mode,
            "total_samples": sum(p.sample_count for p in self.profiles.values())
        }

# Singleton
_baseline_manager = None

def get_baseline_manager() -> BaselineManager:
    global _baseline_manager
    if _baseline_manager is None:
        _baseline_manager = BaselineManager()
    return _baseline_manager
