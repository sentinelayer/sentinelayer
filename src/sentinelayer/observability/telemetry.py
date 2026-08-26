import json
import hashlib
import os
from datetime import datetime
from typing import Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sentinelayer")

class Telemetry:
    def __init__(self):
        self.logs = []
        self.max_logs = 10000
        self.telemetry_key = os.getenv("TELEMETRY_KEY", "change-me")
    
    def log_event(self, event_type: str, data: Dict[str, Any]) -> Dict:
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
            "integrity": self._calculate_integrity(event_type, data)
        }
        
        self.logs.append(event)
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs:]
        
        logger.info(f"Telemetry: {event_type}")
        return event
    
    def _calculate_integrity(self, event_type: str, data: Dict) -> str:
        content = json.dumps({"type": event_type, "data": data}, sort_keys=True)
        return hashlib.sha256(
            (content + self.telemetry_key).encode()
        ).hexdigest()
    
    def verify_integrity(self, event: Dict) -> bool:
        expected = self._calculate_integrity(event["type"], event["data"])
        return expected == event["integrity"]
    
    def get_logs(self, limit: int = 100) -> list:
        return self.logs[-limit:]

telemetry = Telemetry()
