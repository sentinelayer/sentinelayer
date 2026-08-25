import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

@dataclass
class CorrelatedSignal:
    source: str
    target: str
    score: float
    timestamp: float
    details: Dict[str, Any] = field(default_factory=dict)

class SignalCorrelator:
    def __init__(self):
        self.correlations: List[CorrelatedSignal] = []
        self.correlation_window = 60
        self.min_signals_for_correlation = 2
    
    def correlate(self, signals: List[Dict[str, Any]]) -> List[CorrelatedSignal]:
        if len(signals) < self.min_signals_for_correlation:
            return []
        
        results = []
        now = time.time()
        
        for i in range(len(signals)):
            for j in range(i + 1, len(signals)):
                sig_a = signals[i]
                sig_b = signals[j]
                
                if sig_a.get("timestamp", 0) and sig_b.get("timestamp", 0):
                    time_diff = abs(sig_a["timestamp"] - sig_b["timestamp"])
                    if time_diff > self.correlation_window:
                        continue
                
                combined_score = (sig_a.get("score", 0) + sig_b.get("score", 0)) / 2
                boosted_score = min(1.0, combined_score * 1.2)
                
                results.append(CorrelatedSignal(
                    source=sig_a.get("name", "unknown"),
                    target=sig_b.get("name", "unknown"),
                    score=boosted_score,
                    timestamp=now,
                    details={
                        "source_score": sig_a.get("score", 0),
                        "target_score": sig_b.get("score", 0),
                        "time_diff": abs(sig_a.get("timestamp", 0) - sig_b.get("timestamp", 0))
                    }
                ))
        
        self.correlations.extend(results)
        if len(self.correlations) > 100:
            self.correlations = self.correlations[-100:]
        
        return results
    
    def get_recent_correlations(self, limit: int = 50) -> List[CorrelatedSignal]:
        return self.correlations[-limit:]
    
    def clear(self):
        self.correlations = []

_correlator = None

def get_signal_correlator():
    global _correlator
    if _correlator is None:
        _correlator = SignalCorrelator()
    return _correlator
