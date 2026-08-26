from typing import List, Dict
from collections import defaultdict
from datetime import datetime, timedelta

class SignalCorrelator:
    def __init__(self):
        self.signal_cache = defaultdict(list)
        self.correlation_window = 60  # seconds
    
    def add_signal(self, signal_type: str, data: Dict):
        self.signal_cache[signal_type].append({
            "data": data,
            "timestamp": datetime.utcnow()
        })
        self._cleanup()
    
    def correlate(self, context: Dict) -> Dict:
        correlated_signals = {}
        current_time = datetime.utcnow()
        
        for signal_type, signals in self.signal_cache.items():
            relevant = [
                s for s in signals
                if s["data"].get("tenant_id") == context.get("tenant_id")
                and (current_time - s["timestamp"]).seconds < self.correlation_window
            ]
            if relevant:
                correlated_signals[signal_type] = relevant
        
        return self._analyze_correlations(correlated_signals)
    
    def _analyze_correlations(self, signals: Dict) -> Dict:
        result = {
            "total_signals": sum(len(v) for v in signals.values()),
            "signal_types": list(signals.keys()),
            "risk_multiplier": 1.0,
            "priority": "normal"
        }
        
        if len(signals) >= 3:
            result["risk_multiplier"] = 1.5
            result["priority"] = "high"
        elif len(signals) >= 5:
            result["risk_multiplier"] = 2.0
            result["priority"] = "critical"
        
        return result
    
    def _cleanup(self):
        current_time = datetime.utcnow()
        for signal_type in list(self.signal_cache.keys()):
            self.signal_cache[signal_type] = [
                s for s in self.signal_cache[signal_type]
                if (current_time - s["timestamp"]).seconds < self.correlation_window * 2
            ]
            if not self.signal_cache[signal_type]:
                del self.signal_cache[signal_type]

correlator = SignalCorrelator()
