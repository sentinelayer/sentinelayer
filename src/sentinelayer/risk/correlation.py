from typing import Dict, List
from collections import defaultdict
from datetime import datetime

class SignalCorrelator:
    def __init__(self):
        self.signals = defaultdict(list)
    
    def add_signal(self, signal_type: str, data: Dict):
        self.signals[signal_type].append({
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def correlate(self, context: Dict) -> Dict:
        total_signals = sum(len(v) for v in self.signals.values())
        
        # FIX: >=5 dulu, baru >=3
        if total_signals >= 5:
            return {"total_signals": total_signals, "risk_multiplier": 2.0, "priority": "critical"}
        elif total_signals >= 3:
            return {"total_signals": total_signals, "risk_multiplier": 1.5, "priority": "high"}
        else:
            return {"total_signals": total_signals, "risk_multiplier": 1.0, "priority": "normal"}

correlator = SignalCorrelator()
