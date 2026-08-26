from src.sentinelayer.threatintel.provider import get_provider
from src.sentinelayer.risk.correlation import correlator
import logging

logger = logging.getLogger("sentinelayer.threatintel")

class ThreatIntelMiddleware:
    def __init__(self):
        self.provider = get_provider()
    
    async def check_ip(self, ip: str) -> dict:
        try:
            result = await self.provider.check_ip(ip)
            
            # Add to correlation
            if result.get("malicious"):
                correlator.add_signal("threat_intel", {
                    "ip": ip,
                    "score": result.get("score", 0),
                    "source": result.get("source")
                })
            
            return result
        except Exception as e:
            logger.error(f"Threat intel error: {e}")
            return {"malicious": False, "source": "error", "error": str(e)}
    
    async def check_domain(self, domain: str) -> dict:
        try:
            result = await self.provider.check_domain(domain)
            
            if result.get("malicious"):
                correlator.add_signal("threat_intel", {
                    "domain": domain,
                    "source": result.get("source")
                })
            
            return result
        except Exception as e:
            logger.error(f"Threat intel error: {e}")
            return {"malicious": False, "source": "error", "error": str(e)}

threat_intel = ThreatIntelMiddleware()
