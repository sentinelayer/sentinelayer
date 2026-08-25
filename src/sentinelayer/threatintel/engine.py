import time
import json
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from urllib.parse import urlparse
import hashlib

@dataclass
class ThreatIntelResult:
    ip: str
    is_malicious: bool = False
    score: float = 0.0
    source: str = ""
    categories: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

class ThreatIntelEngine:
    """Threat Intelligence Engine with local reputation data"""
    
    def __init__(self):
        # Local threat database (mock)
        self.malicious_ips = {
            "192.168.1.100": {"score": 0.9, "categories": ["scanner", "malware"]},
            "10.0.0.50": {"score": 0.8, "categories": ["botnet", "spam"]},
            "172.16.0.25": {"score": 0.7, "categories": ["scanner"]},
        }
        self.malicious_domains = {
            "evil.com": {"score": 0.9, "categories": ["malware", "phishing"]},
            "malware.test": {"score": 0.8, "categories": ["malware"]},
        }
        self.malicious_asns = {"AS12345": {"score": 0.8, "categories": ["hosting_provider"]}}
        self.malicious_countries = {"KP": {"score": 0.7, "categories": ["state_sponsored"]}}
        
        # Cache
        self.cache: Dict[str, ThreatIntelResult] = {}
        self.cache_ttl = 300  # 5 minutes
    
    def check_ip(self, ip: str) -> ThreatIntelResult:
        """Check IP reputation"""
        cache_key = f"ip:{ip}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached.timestamp < self.cache_ttl:
                return cached
        
        result = ThreatIntelResult(ip=ip)
        if ip in self.malicious_ips:
            data = self.malicious_ips[ip]
            result.is_malicious = True
            result.score = data.get("score", 0.5)
            result.categories = data.get("categories", [])
            result.source = "local_db"
            result.details = data
        
        # Check for private IP (always low risk)
        if ip.startswith("10.") or ip.startswith("192.168.") or ip.startswith("172.16."):
            result.score = min(result.score, 0.2)
            result.is_malicious = False
        
        self.cache[cache_key] = result
        return result
    
    def check_domain(self, domain: str) -> ThreatIntelResult:
        """Check domain reputation"""
        cache_key = f"domain:{domain}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached.timestamp < self.cache_ttl:
                return cached
        
        result = ThreatIntelResult(ip=domain)
        if domain in self.malicious_domains:
            data = self.malicious_domains[domain]
            result.is_malicious = True
            result.score = data.get("score", 0.5)
            result.categories = data.get("categories", [])
            result.source = "local_db"
            result.details = data
        
        self.cache[cache_key] = result
        return result
    
    def check_asn(self, asn: str) -> ThreatIntelResult:
        """Check ASN reputation"""
        cache_key = f"asn:{asn}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached.timestamp < self.cache_ttl:
                return cached
        
        result = ThreatIntelResult(ip=asn)
        if asn in self.malicious_asns:
            data = self.malicious_asns[asn]
            result.is_malicious = True
            result.score = data.get("score", 0.5)
            result.categories = data.get("categories", [])
            result.source = "local_db"
            result.details = data
        
        self.cache[cache_key] = result
        return result
    
    def check_geo(self, country_code: str) -> ThreatIntelResult:
        """Check country reputation"""
        cache_key = f"geo:{country_code}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached.timestamp < self.cache_ttl:
                return cached
        
        result = ThreatIntelResult(ip=country_code)
        if country_code in self.malicious_countries:
            data = self.malicious_countries[country_code]
            result.is_malicious = True
            result.score = data.get("score", 0.5)
            result.categories = data.get("categories", [])
            result.source = "local_db"
            result.details = data
        
        self.cache[cache_key] = result
        return result
    
    def enrich_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich request with threat intelligence"""
        enriched = request_data.copy()
        
        # Get client IP
        client_ip = request_data.get("client_ip", "")
        if client_ip:
            ip_result = self.check_ip(client_ip)
            enriched["ip_reputation"] = {
                "score": ip_result.score,
                "is_malicious": ip_result.is_malicious,
                "categories": ip_result.categories,
                "source": ip_result.source
            }
        
        # Get domain from URL
        url = request_data.get("url", "")
        if url:
            parsed = urlparse(url)
            domain = parsed.netloc
            if domain:
                domain_result = self.check_domain(domain)
                enriched["domain_reputation"] = {
                    "score": domain_result.score,
                    "is_malicious": domain_result.is_malicious,
                    "categories": domain_result.categories,
                    "source": domain_result.source
                }
        
        return enriched

def get_threat_intel() -> ThreatIntelEngine:
    return ThreatIntelEngine()
_threat_intel = None

def get_threat_intel():
    global _threat_intel
    if _threat_intel is None:
        _threat_intel = ThreatIntelEngine()
    return _threat_intel
