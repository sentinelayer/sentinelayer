from typing import Dict, List

class ApplicabilityEngine:
    def __init__(self):
        self.frameworks = {
            "soc2": {"applicable_to": ["enterprise", "saas", "fintech"], "controls": ["access_control", "audit_log", "encryption", "backup", "incident_response"]},
            "iso27001": {"applicable_to": ["enterprise", "saas", "fintech", "government"], "controls": ["access_control", "audit_log", "encryption", "backup", "incident_response", "training"]},
            "gdpr": {"applicable_to": ["any"], "controls": ["data_classification", "retention", "deletion", "consent", "breach_notification"]},
            "pci_dss": {"applicable_to": ["fintech", "ecommerce"], "controls": ["cardholder_data", "tokenization", "encryption", "access_control", "audit_log", "mfa"]}
        }

    def determine_applicability(self, customer_type: str, industry: str, data_type: str, region: str) -> Dict:
        applicable = []
        for framework_id, config in self.frameworks.items():
            if "any" in config.get("applicable_to", []) or customer_type in config.get("applicable_to", []) or industry in config.get("applicable_to", []):
                applicable.append({"framework": framework_id, "controls": config.get("controls", [])})
        return {"customer_type": customer_type, "industry": industry, "data_type": data_type, "region": region, "applicable_frameworks": applicable}
