from abc import ABC, abstractmethod
import httpx
import os
from typing import Dict

class ThreatIntelProvider(ABC):
    @abstractmethod
    async def check_ip(self, ip: str) -> Dict:
        pass
    
    @abstractmethod
    async def check_domain(self, domain: str) -> Dict:
        pass

class VirusTotalProvider(ThreatIntelProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.virustotal.com/api/v3"
    
    async def check_ip(self, ip: str) -> Dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/ip_addresses/{ip}",
                headers={"x-apikey": self.api_key}
            )
            if resp.status_code == 200:
                data = resp.json()
                stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                total = sum(stats.values())
                if total == 0:
                    return {"malicious": False, "source": "virustotal", "score": 0}
                malicious = stats.get("malicious", 0)
                return {
                    "malicious": malicious > 0,
                    "source": "virustotal",
                    "score": (malicious / total) * 100,
                    "stats": stats
                }
            return {"malicious": False, "source": "virustotal", "error": "API error"}

    async def check_domain(self, domain: str) -> Dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/domains/{domain}",
                headers={"x-apikey": self.api_key}
            )
            if resp.status_code == 200:
                data = resp.json()
                stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                malicious = stats.get("malicious", 0)
                return {
                    "malicious": malicious > 0,
                    "source": "virustotal",
                    "malicious_count": malicious
                }
            return {"malicious": False, "source": "virustotal", "error": "API error"}

class MockProvider(ThreatIntelProvider):
    async def check_ip(self, ip: str) -> Dict:
        if ip.startswith(("192.168.", "10.", "172.16.", "127.")):
            return {"malicious": False, "source": "mock", "note": "private IP"}
        return {"malicious": False, "source": "mock", "note": "no threat intel configured"}

    async def check_domain(self, domain: str) -> Dict:
        return {"malicious": False, "source": "mock", "note": "no threat intel configured"}

def get_provider() -> ThreatIntelProvider:
    provider_type = os.getenv("THREAT_INTEL_PROVIDER", "mock")
    
    if provider_type == "virustotal":
        api_key = os.getenv("VIRUSTOTAL_API_KEY")
        if not api_key:
            raise ValueError("VIRUSTOTAL_API_KEY not set")
        return VirusTotalProvider(api_key)
    
    return MockProvider()
