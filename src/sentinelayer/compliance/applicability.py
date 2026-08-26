from datetime import datetime
from typing import Dict, List

class ApplicabilityEngine:
    def __init__(self):
        self.frameworks = {
            "soc2": {
                "applicable_to": ["enterprise", "saas", "fintech"],
                "controls": ["access_control", "audit_log", "encryption", "backup", "incident_response"],
                "priority": "HIGH"
            },
            "iso27001": {
                "applicable_to": ["enterprise", "saas", "fintech", "government"],
                "controls": ["access_control", "audit_log", "encryption", "backup", "incident_response", "training"],
                "priority": "HIGH"
            },
            "gdpr": {
                "applicable_to": ["any"],
                "controls": ["data_classification", "retention", "deletion", "consent", "breach_notification"],
                "priority": "HIGH"
            }
        }

    def determine_applicability(self, customer_type: str, industry: str, data_type: str, region: str) -> Dict:
        applicable = []
        for framework_id, config in self.frameworks.items():
            applicable_to = config.get("applicable_to", [])
            if "any" in applicable_to or customer_type in applicable_to or industry in applicable_to:
                applicable.append({
                    "framework": framework_id,
                    "reason": f"Applies to {customer_type}",
                    "controls": config.get("controls", []),
                    "priority": config.get("priority", "MEDIUM"),
                    "valid_until": (datetime.utcnow().replace(year=datetime.utcnow().year + 1)).isoformat()
                })
        return {
            "customer_type": customer_type,
            "industry": industry,
            "data_type": data_type,
            "region": region,
            "applicable_frameworks": applicable,
            "total_frameworks": len(applicable),
            "evaluated_at": datetime.utcnow().isoformat()
        }

applicability = ApplicabilityEngine()
