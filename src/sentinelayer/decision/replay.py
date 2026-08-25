import time
import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

@dataclass
class DecisionRecord:
    request_id: str
    decision: str
    risk_score: float
    timestamp: float
    context: Dict[str, Any]

class DecisionReplay:
    def __init__(self):
        self.history: List[DecisionRecord] = []
        self.max_history = 1000
        self.log_file = "private/decision_history.json"
        self.load_history()
    
    def record(self, request_id: str, decision: str, risk_score: float, context: Dict[str, Any]):
        record = DecisionRecord(request_id, decision, risk_score, time.time(), context)
        self.history.append(record)
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        self.save_history()
    
    def replay(self, request_id: str) -> Optional[DecisionRecord]:
        for record in reversed(self.history):
            if record.request_id == request_id:
                return record
        return None
    
    def get_recent(self, limit: int = 50) -> List[DecisionRecord]:
        return self.history[-limit:]
    
    def save_history(self):
        os.makedirs("private", exist_ok=True)
        with open(self.log_file, "w") as f:
            json.dump([r.__dict__ for r in self.history], f, indent=2, default=str)
    
    def load_history(self):
        try:
            with open(self.log_file, "r") as f:
                data = json.load(f)
                self.history = [DecisionRecord(**r) for r in data]
        except:
            pass

_decision_replay = None

def get_decision_replay():
    global _decision_replay
    if _decision_replay is None:
        _decision_replay = DecisionReplay()
    return _decision_replay
