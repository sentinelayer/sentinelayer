import os
from typing import Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("sentinelayer.safemode")

class SafeMode:
    def __init__(self):
        self.mode = os.getenv("DECISION_MODE", "production")
        self.override_enabled = False
        self.override_reason = None
        self.override_until = None
    
    def is_safe_mode(self) -> bool:
        return self.mode == "safe" or self.mode == "monitor-only"
    
    def is_monitor_only(self) -> bool:
        return self.mode == "monitor-only"
    
    def is_blocking_enabled(self) -> bool:
        if self.mode == "monitor-only":
            return False
        if self.mode == "safe":
            return True
        return True
    
    def process_decision(self, decision: Dict) -> Dict:
        if self.mode == "monitor-only":
            return {
                **decision,
                "action": "MONITOR_ONLY",
                "blocked": False,
                "original_action": decision.get("action"),
                "reason": "Monitor-only mode enabled"
            }
        
        if self.mode == "safe":
            if decision.get("action") == "BLOCK":
                return {
                    **decision,
                    "action": "CHALLENGE",
                    "blocked": False,
                    "reason": "Safe mode: BLOCK converted to CHALLENGE"
                }
        
        return decision
    
    def set_override(self, enabled: bool, reason: str = None, duration_hours: int = 1):
        self.override_enabled = enabled
        self.override_reason = reason
        if enabled:
            self.override_until = datetime.utcnow() + timedelta(hours=duration_hours)
    
    def is_override_active(self) -> bool:
        if not self.override_enabled:
            return False
        if self.override_until and datetime.utcnow() > self.override_until:
            self.override_enabled = False
            return False
        return True

safe_mode = SafeMode()
