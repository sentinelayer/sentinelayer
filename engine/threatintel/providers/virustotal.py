import os
import httpx

class VirusTotalProvider:
    def __init__(self):
        self.api_key = os.getenv("VIRUSTOTAL_API_KEY")
        self.base_url = "https://www.virustotal.com/api/v3"

    async def check_ip(self, ip: str) -> dict:
        if not self.api_key:
            return {"malicious": False, "source": "virustotal", "error": "API key missing"}
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/ip_addresses/{ip}",
                headers={"x-apikey": self.api_key}
            )
            if resp.status_code == 200:
                data = resp.json()
                stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                malicious = stats.get("malicious", 0)
                return {"malicious": malicious > 0, "source": "virustotal", "malicious_count": malicious}
            return {"malicious": False, "source": "virustotal", "error": "API error"}

    async def check_domain(self, domain: str) -> dict:
        if not self.api_key:
            return {"malicious": False, "source": "virustotal", "error": "API key missing"}
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/domains/{domain}",
                headers={"x-apikey": self.api_key}
            )
            if resp.status_code == 200:
                data = resp.json()
                stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                malicious = stats.get("malicious", 0)
                return {"malicious": malicious > 0, "source": "virustotal", "malicious_count": malicious}
            return {"malicious": False, "source": "virustotal", "error": "API error"}
