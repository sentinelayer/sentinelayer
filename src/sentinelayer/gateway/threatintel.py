import os
import time
from src.sentinelayer.threatintel.provider import get_provider

class ThreatIntelMiddleware:
    def __init__(self):
        self._provider = None
        self.cache = {}
        self.ttl = int(os.getenv("THREAT_INTEL_TTL", "300"))

    @property
    def provider(self):
        if self._provider is None:
            try:
                self._provider = get_provider()
            except ValueError:
                self._provider = None
        return self._provider

    async def check_ip(self, ip: str):
        cache_key = f"ip:{ip}"
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if time.time() - entry["timestamp"] < self.ttl:
                return entry["result"]

        if self.provider is None:
            return {"malicious": False, "source": "disabled"}

        result = await self.provider.check_ip(ip)
        self.cache[cache_key] = {"result": result, "timestamp": time.time()}
        return result

    async def check_domain(self, domain: str):
        cache_key = f"domain:{domain}"
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if time.time() - entry["timestamp"] < self.ttl:
                return entry["result"]

        if self.provider is None:
            return {"malicious": False, "source": "disabled"}

        result = await self.provider.check_domain(domain)
        self.cache[cache_key] = {"result": result, "timestamp": time.time()}
        return result

threat_intel = ThreatIntelMiddleware()
