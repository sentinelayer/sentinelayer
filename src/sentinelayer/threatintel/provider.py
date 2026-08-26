import os
from abc import ABC, abstractmethod
import httpx

class ThreatIntelProvider(ABC):
    @abstractmethod
    async def check_ip(self, ip: str) -> dict:
        pass
    
    @abstractmethod
    async def check_domain(self, domain: str) -> dict:
        pass

class VirusTotalProvider(ThreatIntelProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.virustotal.com/api/v3"
    
    async def check_ip(self, ip: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/ip_addresses/{ip}", headers={"x-apikey": self.api_key})
            if resp.status_code == 200:
                data = resp.json()
                stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                malicious = stats.get("malicious", 0)
                return {"malicious": malicious > 0, "source": "virustotal", "score": malicious}
            return {"malicious": False, "source": "virustotal", "error": "API error"}
    
    async def check_domain(self, domain: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/domains/{domain}", headers={"x-apikey": self.api_key})
            if resp.status_code == 200:
                data = resp.json()
                stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                malicious = stats.get("malicious", 0)
                return {"malicious": malicious > 0, "source": "virustotal", "malicious_count": malicious}
            return {"malicious": False, "source": "virustotal", "error": "API error"}

class AbuseIPDBProvider(ThreatIntelProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.abuseipdb.com/api/v2"
    
    async def check_ip(self, ip: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/check", params={"ipAddress": ip, "maxAgeInDays": 90}, headers={"Key": self.api_key, "Accept": "application/json"})
            if resp.status_code == 200:
                data = resp.json()
                score = data.get("data", {}).get("abuseConfidenceScore", 0)
                return {"malicious": score > 30, "source": "abuseipdb", "score": score}
            return {"malicious": False, "source": "abuseipdb", "error": "API error"}
    
    async def check_domain(self, domain: str) -> dict:
        return {"malicious": False, "source": "abuseipdb", "error": "Domain check not supported"}

def get_provider() -> ThreatIntelProvider:
    provider_type = os.getenv("THREAT_INTEL_PROVIDER", "virustotal")
    
    if provider_type == "virustotal":
        api_key = os.getenv("VIRUSTOTAL_API_KEY")
        if not api_key:
            raise ValueError("VIRUSTOTAL_API_KEY not set")
        return VirusTotalProvider(api_key)
    
    if provider_type == "abuseipdb":
        api_key = os.getenv("ABUSEIPDB_API_KEY")
        if not api_key:
            raise ValueError("ABUSEIPDB_API_KEY not set")
        return AbuseIPDBProvider(api_key)
    
    raise ValueError(f"Unknown provider: {provider_type}")
