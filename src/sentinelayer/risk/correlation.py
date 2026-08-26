from typing import Dict
from collections import defaultdict

class SignalCorrelator:
    def __init__(self):
        self.signals = defaultdict(lambda: defaultdict(list))

    def add_signal(self, signal_type: str, data: Dict):
        tenant_id = data.get("tenant_id", "global")
        self.signals[tenant_id][signal_type].append(data)

    def correlate(self, context: Dict) -> Dict:
        tenant_id = context.get("tenant_id", "global")
        tenant_signals = self.signals.get(tenant_id, {})

        total_signals = sum(len(v) for v in tenant_signals.values())

        if total_signals >= 5:
            return {"total_signals": total_signals, "risk_multiplier": 2.0, "priority": "critical"}
        elif total_signals >= 3:
            return {"total_signals": total_signals, "risk_multiplier": 1.5, "priority": "high"}
        else:
            return {"total_signals": total_signals, "risk_multiplier": 1.0, "priority": "normal"}

correlator = SignalCorrelator()
