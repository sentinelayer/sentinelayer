import os
import logging
from src.sentinelayer.threatintel.provider import get_provider

logger = logging.getLogger("sentinelayer.threatintel")

class ThreatIntelMiddleware:
    def __init__(self):
        self._provider = None

    @property
    def provider(self):
        if self._provider is None:
            try:
                self._provider = get_provider()
            except ValueError as e:
                logger.warning(f"Threat intel disabled: {e}")
                self._provider = None
        return self._provider

    async def check_ip(self, ip: str):
        if self.provider is None:
            return {"malicious": False, "source": "disabled"}
        return await self.provider.check_ip(ip)

    async def check_domain(self, domain: str):
        if self.provider is None:
            return {"malicious": False, "source": "disabled"}
        return await self.provider.check_domain(domain)

threat_intel = ThreatIntelMiddleware()
