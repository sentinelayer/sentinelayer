import time
import requests
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class ThreatIntelResult:
    ip: str
    is_malicious: bool = False
    score: float = 0.0
    source: str = ""
    categories: list = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

class ThreatIntelEngine:
    def __init__(self):
        self.cache: Dict[str, ThreatIntelResult] = {}
        self.cache_ttl = 300
        self.api_key = os.getenv("THREAT_INTEL_API_KEY", "")
        self.provider = os.getenv("THREAT_INTEL_PROVIDER", "local")
    
    def check_ip(self, ip: str) -> ThreatIntelResult:
        cache_key = f"ip:{ip}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached.timestamp < self.cache_ttl:
                return cached
        
        result = ThreatIntelResult(ip=ip)
        
        if self.provider == "local":
            malicious_ips = {
                "192.168.1.100": {"score": 0.9, "categories": ["scanner"]},
                "10.0.0.50": {"score": 0.8, "categories": ["botnet"]},
            }
            if ip in malicious_ips:
                data = malicious_ips[ip]
                result.is_malicious = True
                result.score = data.get("score", 0.5)
                result.categories = data.get("categories", [])
                result.source = "local_db"
                result.details = data
        
        self.cache[cache_key] = result
        return result
    
    def check_domain(self, domain: str) -> ThreatIntelResult:
        result = ThreatIntelResult(ip=domain)
        malicious_domains = {"evil.com": {"score": 0.9, "categories": ["malware"]}}
        if domain in malicious_domains:
            data = malicious_domains[domain]
            result.is_malicious = True
            result.score = data.get("score", 0.5)
            result.categories = data.get("categories", [])
            result.source = "local_db"
            result.details = data
        return result

_threat_intel = None

def get_threat_intel():
    global _threat_intel
    if _threat_intel is None:
        _threat_intel = ThreatIntelEngine()
    return _threat_intel
