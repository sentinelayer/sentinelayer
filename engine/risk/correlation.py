from collections import defaultdict
from datetime import datetime, timedelta


class RiskCorrelation:
    def __init__(self):
        self.signals = defaultdict(list)
        self.correlation_window = 60

    def add_signal(self, tenant_id: str, signal_type: str, data: dict):
        self.signals[tenant_id].append({
            "type": signal_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        })
        self._cleanup(tenant_id)

    def _cleanup(self, tenant_id: str):
        cutoff = datetime.utcnow() - timedelta(seconds=self.correlation_window)
        self.signals[tenant_id] = [
            s for s in self.signals[tenant_id]
            if datetime.fromisoformat(s["timestamp"]) > cutoff
        ]

    def correlate(self, tenant_id: str) -> dict:
        signals = self.signals.get(tenant_id, [])
        if not signals:
            return {"risk_multiplier": 1.0, "signal_count": 0}

        types = set(s["type"] for s in signals)
        multiplier = 1.0
        if len(types) >= 5:
            multiplier = 2.0
        elif len(types) >= 3:
            multiplier = 1.5

        # Dedup: unique types only
        return {
            "risk_multiplier": multiplier,
            "signal_count": len(signals),
            "unique_types": len(types),
            "types": list(types)
        }
