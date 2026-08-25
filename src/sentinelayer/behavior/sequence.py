import time
import json
from typing import List, Dict, Any, Optional
from collections import deque
from dataclasses import dataclass, field

@dataclass
class SequenceRule:
    id: str
    name: str
    pattern: List[str]
    window_seconds: int
    severity: str
    description: str = ""

@dataclass
class SequenceMatch:
    rule_id: str
    rule_name: str
    events: List[Dict]
    timestamp: float
    severity: str

class SequenceDetector:
    def __init__(self):
        self.user_sequences: Dict[str, deque] = {}
        self.max_sequence_length = 20
        self.rules: List[SequenceRule] = []
        self.matches: List[SequenceMatch] = []
        self.load_default_rules()
    
    def load_default_rules(self):
        self.rules.extend([
            SequenceRule(
                id="SEQ-001",
                name="Fraudulent Payment Flow",
                pattern=["login", "add_payment_method", "apply_coupon", "refund_request"],
                window_seconds=300,
                severity="high",
                description="Suspicious refund pattern after adding payment method"
            ),
            SequenceRule(
                id="SEQ-002",
                name="Rapid Account Changes",
                pattern=["login", "change_password", "change_email", "logout"],
                window_seconds=60,
                severity="medium",
                description="Rapid account changes in short time"
            ),
            SequenceRule(
                id="SEQ-003",
                name="Credential Stuffing Pattern",
                pattern=["login_failed", "login_failed", "login_failed", "login_success"],
                window_seconds=30,
                severity="high",
                description="Multiple failed logins followed by success"
            ),
            SequenceRule(
                id="SEQ-004",
                name="Data Exfiltration",
                pattern=["login", "list_orders", "get_order", "get_order", "get_order"],
                window_seconds=60,
                severity="critical",
                description="Rapid order retrieval pattern"
            ),
        ])
    
    def get_user_key(self, user_id: str, tenant_id: str) -> str:
        return f"{tenant_id}:{user_id}"
    
    def add_event(self, user_id: str, tenant_id: str, event_type: str, details: Dict = None):
        key = self.get_user_key(user_id, tenant_id)
        
        if key not in self.user_sequences:
            self.user_sequences[key] = deque(maxlen=self.max_sequence_length)
        
        event = {
            "type": event_type,
            "timestamp": time.time(),
            "details": details or {}
        }
        self.user_sequences[key].append(event)
        
        return self.detect_sequences(user_id, tenant_id)
    
    def detect_sequences(self, user_id: str, tenant_id: str) -> List[SequenceMatch]:
        key = self.get_user_key(user_id, tenant_id)
        
        if key not in self.user_sequences:
            return []
        
        events = list(self.user_sequences[key])
        matches = []
        now = time.time()
        
        for rule in self.rules:
            match = self._check_pattern(events, rule)
            if match:
                matches.append(match)
                self.matches.append(match)
        
        return matches
    
    def _check_pattern(self, events: List[Dict], rule: SequenceRule) -> Optional[SequenceMatch]:
        if len(events) < len(rule.pattern):
            return None
        
        now = time.time()
        
        for i in range(len(events) - len(rule.pattern) + 1):
            window_start = events[i]["timestamp"]
            window_end = events[i + len(rule.pattern) - 1]["timestamp"]
            
            if window_end - window_start > rule.window_seconds:
                continue
            
            match = True
            for j, expected_type in enumerate(rule.pattern):
                if events[i + j]["type"] != expected_type:
                    match = False
                    break
            
            if match:
                return SequenceMatch(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    events=events[i:i + len(rule.pattern)],
                    timestamp=now,
                    severity=rule.severity
                )
        
        return None
    
    def get_user_sequence(self, user_id: str, tenant_id: str) -> List[Dict]:
        key = self.get_user_key(user_id, tenant_id)
        if key in self.user_sequences:
            return list(self.user_sequences[key])
        return []
    
    def get_recent_matches(self, limit: int = 50) -> List[SequenceMatch]:
        return self.matches[-limit:]
    
    def clear_user_sequence(self, user_id: str, tenant_id: str):
        key = self.get_user_key(user_id, tenant_id)
        if key in self.user_sequences:
            self.user_sequences[key].clear()

_sequence_detector = None

def get_sequence_detector():
    global _sequence_detector
    if _sequence_detector is None:
        _sequence_detector = SequenceDetector()
    return _sequence_detector
