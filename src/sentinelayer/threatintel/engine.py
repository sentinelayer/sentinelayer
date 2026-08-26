# Threat Intelligence Engine - uses provider abstraction
from src.sentinelayer.threatintel.provider import get_provider
import logging

logger = logging.getLogger("sentinelayer.threatintel")

class ThreatIntelEngine:
    def __init__(self):
        self.provider = get_provider()
    
    async def check_ip(self, ip: str):
        return await self.provider.check_ip(ip)
    
    async def check_domain(self, domain: str):
        return await self.provider.check_domain(domain)

engine = ThreatIntelEngine()
