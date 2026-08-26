from typing import List, Dict
from collections import defaultdict
from datetime import datetime, timedelta

class SequenceDetector:
    def __init__(self):
        self.sequences = defaultdict(list)
        self.patterns = {
            "brute_force": ["login_failed", "login_failed", "login_failed", "login_success"],
            "credential_stuffing": ["login_failed", "login_failed", "login_failed", "login_failed"],
            "recon": ["page_view", "page_view", "page_view", "api_scan"],
            "data_exfil": ["download", "download", "download", "bulk_export"]
        }
    
    def add_event(self, user_id: str, event_type: str, data: Dict):
        self.sequences[user_id].append({
            "event": event_type,
            "data": data,
            "timestamp": datetime.utcnow()
        })
        if len(self.sequences[user_id]) > 100:
            self.sequences[user_id] = self.sequences[user_id][-100:]
    
    def detect(self, user_id: str) -> List[Dict]:
        events = self.sequences.get(user_id, [])
        if len(events) < 3:
            return []
        
        recent = [e["event"] for e in events[-10:]]
        detected = []
        
        for pattern_name, pattern in self.patterns.items():
            if self._matches_pattern(recent, pattern):
                detected.append({
                    "pattern": pattern_name,
                    "confidence": self._calculate_confidence(recent, pattern),
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        return detected
    
    def _matches_pattern(self, events: List[str], pattern: List[str]) -> bool:
        if len(events) < len(pattern):
            return False
        return events[-len(pattern):] == pattern
    
    def _calculate_confidence(self, events: List[str], pattern: List[str]) -> float:
        matches = sum(1 for i, p in enumerate(pattern) if events[-len(pattern):][i] == p)
        return min(1.0, matches / len(pattern))

sequence_detector = SequenceDetector()
