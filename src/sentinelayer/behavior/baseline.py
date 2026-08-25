import time
import json
import hashlib
import redis
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import statistics

@dataclass
class BaselineProfile:
    endpoint: str
    method: str
    user_id: str
    tenant_id: str
    sample_count: int = 0
    avg_response_time: float = 0.0
    avg_request_size: float = 0.0
    avg_response_size: float = 0.0
    status_codes: Dict[int, int] = field(default_factory=dict)
    time_series: List[float] = field(default_factory=list)
    last_updated: float = field(default_factory=time.time)
    is_stable: bool = False
    min_samples_required: int = 100

    def to_dict(self) -> Dict:
        return {
            "endpoint": self.endpoint,
            "method": self.method,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "sample_count": self.sample_count,
            "avg_response_time": self.avg_response_time,
            "avg_request_size": self.avg_request_size,
            "avg_response_size": self.avg_response_size,
            "status_codes": self.status_codes,
            "time_series": self.time_series[-100:],
            "last_updated": self.last_updated,
            "is_stable": self.is_stable,
            "min_samples_required": self.min_samples_required
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "BaselineProfile":
        return cls(
            endpoint=data["endpoint"],
            method=data["method"],
            user_id=data["user_id"],
            tenant_id=data["tenant_id"],
            sample_count=data["sample_count"],
            avg_response_time=data["avg_response_time"],
            avg_request_size=data["avg_request_size"],
            avg_response_size=data["avg_response_size"],
            status_codes=data.get("status_codes", {}),
            time_series=data.get("time_series", []),
            last_updated=data.get("last_updated", time.time()),
            is_stable=data.get("is_stable", False),
            min_samples_required=data.get("min_samples_required", 100)
        )
    
    def update(self, request_data: Dict[str, Any]):
        self.sample_count += 1
        rt = request_data.get("response_time", 0)
        self.avg_response_time = ((self.avg_response_time * (self.sample_count - 1)) + rt) / self.sample_count
        req_size = request_data.get("request_size", 0)
        self.avg_request_size = ((self.avg_request_size * (self.sample_count - 1)) + req_size) / self.sample_count
        resp_size = request_data.get("response_size", 0)
        self.avg_response_size = ((self.avg_response_size * (self.sample_count - 1)) + resp_size) / self.sample_count
        status = request_data.get("status_code", 200)
        self.status_codes[status] = self.status_codes.get(status, 0) + 1
        self.time_series.append(rt)
        if len(self.time_series) > 100:
            self.time_series.pop(0)
        if self.sample_count >= self.min_samples_required and len(self.time_series) >= 30:
            self.is_stable = True
        self.last_updated = time.time()
    
    def get_anomaly_score(self, request_data: Dict[str, Any]) -> float:
        if not self.is_stable or self.sample_count < self.min_samples_required:
            return 0.5
        score = 0.0
        factors = 0
        rt = request_data.get("response_time", 0)
        if rt > 0 and self.avg_response_time > 0:
            rt_ratio = rt / self.avg_response_time
            if rt_ratio > 3.0:
                score += 0.3
                factors += 1
            elif rt_ratio > 2.0:
                score += 0.15
                factors += 1
        req_size = request_data.get("request_size", 0)
        if req_size > 0 and self.avg_request_size > 0:
            size_ratio = req_size / self.avg_request_size
            if size_ratio > 5.0:
                score += 0.2
                factors += 1
            elif size_ratio > 3.0:
                score += 0.1
                factors += 1
        status = request_data.get("status_code", 200)
        if status in [400, 401, 403, 404, 500]:
            score += 0.2
            factors += 1
        return min(1.0, score)

class BaselineManager:
    def __init__(self):
        self.learning_mode = True
        self.learning_samples = 100
        self.redis_client = None
        self._init_redis()
        self.profiles: Dict[str, BaselineProfile] = {}
        self.load_all_profiles()
    
    def _init_redis(self):
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            print("✅ Baseline: Redis connected")
        except Exception as e:
            self.redis_client = None
            print("⚠️ Baseline: Redis not available, using in-memory only")
    
    def _get_redis_key(self, profile_key: str) -> str:
        return f"baseline:profile:{profile_key}"
    
    def get_profile_key(self, endpoint: str, method: str, user_id: str, tenant_id: str) -> str:
        raw = f"{tenant_id}:{user_id}:{method}:{endpoint}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]
    
    def _save_to_redis(self, profile_key: str, profile: BaselineProfile):
        if self.redis_client:
            key = self._get_redis_key(profile_key)
            self.redis_client.setex(key, 86400 * 30, json.dumps(profile.to_dict()))
    
    def _load_from_redis(self, profile_key: str) -> Optional[BaselineProfile]:
        if self.redis_client:
            key = self._get_redis_key(profile_key)
            data = self.redis_client.get(key)
            if data:
                try:
                    return BaselineProfile.from_dict(json.loads(data))
                except Exception as e:
                    pass
        return None
    
    def load_all_profiles(self):
        if not self.redis_client:
            return
        keys = self.redis_client.keys("baseline:profile:*")
        for key in keys:
            data = self.redis_client.get(key)
            if data:
                try:
                    profile = BaselineProfile.from_dict(json.loads(data))
                    pk = self.get_profile_key(profile.endpoint, profile.method, profile.user_id, profile.tenant_id)
                    self.profiles[pk] = profile
                except Exception as e:
                    pass
        print(f"✅ Loaded {len(self.profiles)} baseline profiles from Redis")
    
    def record_request(self, request_data: Dict[str, Any]) -> BaselineProfile:
        pk = self.get_profile_key(
            request_data.get("endpoint", ""),
            request_data.get("method", "GET"),
            request_data.get("user_id", "unknown"),
            request_data.get("tenant_id", "default")
        )
        
        if pk not in self.profiles:
            # Coba load dari Redis dulu
            loaded = self._load_from_redis(pk)
            if loaded:
                self.profiles[pk] = loaded
            else:
                self.profiles[pk] = BaselineProfile(
                    endpoint=request_data.get("endpoint", ""),
                    method=request_data.get("method", "GET"),
                    user_id=request_data.get("user_id", "unknown"),
                    tenant_id=request_data.get("tenant_id", "default")
                )
        
        self.profiles[pk].update(request_data)
        self._save_to_redis(pk, self.profiles[pk])
        
        stable_count = sum(1 for p in self.profiles.values() if p.is_stable)
        if len(self.profiles) > 0 and stable_count / len(self.profiles) >= 0.8:
            self.learning_mode = False
        
        return self.profiles[pk]
    
    def detect_anomaly(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        pk = self.get_profile_key(
            request_data.get("endpoint", ""),
            request_data.get("method", "GET"),
            request_data.get("user_id", "unknown"),
            request_data.get("tenant_id", "default")
        )
        
        if pk not in self.profiles:
            return {
                "is_anomaly": False,
                "score": 0.5,
                "reason": "No baseline profile yet",
                "confidence": 0.2
            }
        
        profile = self.profiles[pk]
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
            "total_samples": sum(p.sample_count for p in self.profiles.values()),
            "redis_available": self.redis_client is not None
        }

_baseline_manager = None

def get_baseline_manager() -> BaselineManager:
    global _baseline_manager
    if _baseline_manager is None:
        _baseline_manager = BaselineManager()
    return _baseline_manager
from sentinelayer.behavior.sequence import get_sequence_detector

class BaselineManager:
    def __init__(self):
        self.learning_mode = True
        self.learning_samples = 100
        self.redis_client = None
        self.sequence_detector = get_sequence_detector()
        self._init_redis()
        self.profiles: Dict[str, BaselineProfile] = {}
        self.load_all_profiles()
    
    def record_sequence_event(self, user_id: str, tenant_id: str, event_type: str, details: Dict = None):
        return self.sequence_detector.add_event(user_id, tenant_id, event_type, details)
    
    def get_user_sequence(self, user_id: str, tenant_id: str):
        return self.sequence_detector.get_user_sequence(user_id, tenant_id)
    
    def get_sequence_matches(self):
        return self.sequence_detector.get_recent_matches()
