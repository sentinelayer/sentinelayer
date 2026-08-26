# WARNING: Hardcoded threat intel removed
# Use external provider (VirusTotal, AbuseIPDB, etc.)
class ThreatDatabase:
    def __init__(self):
        self.provider = None
    
    def set_provider(self, provider):
        self.provider = provider
    
    def check_ip(self, ip):
        if not self.provider:
            return {"malicious": False, "source": "none"}
        return self.provider.check_ip(ip)
