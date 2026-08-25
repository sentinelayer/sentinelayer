import time
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class CorrelatedSignal:
    source: str
    target: str
    score: float
    timestamp: float
    details: Dict[str, Any]

class SignalCorrelator:
    def __init__(self):
        self.correlation_window = 60
    
    def correlate(self, signals: List[Dict[str, Any]]) -> List[CorrelatedSignal]:
        results = []
        for i in range(len(signals)):
            for j in range(i + 1, len(signals)):
                sig_a = signals[i]
                sig_b = signals[j]
                if abs(sig_a.get("timestamp", 0) - sig_b.get("timestamp", 0)) > self.correlation_window:
                    continue
                combined_score = (sig_a.get("score", 0) + sig_b.get("score", 0)) / 2
                boosted_score = min(1.0, combined_score * 1.2)
                results.append(CorrelatedSignal(
                    source=sig_a.get("name", "unknown"),
                    target=sig_b.get("name", "unknown"),
                    score=boosted_score,
                    timestamp=time.time(),
                    details={"source_score": sig_a.get("score", 0), "target_score": sig_b.get("score", 0)}
                ))
        return results

def get_signal_correlator():
    return SignalCorrelator()
