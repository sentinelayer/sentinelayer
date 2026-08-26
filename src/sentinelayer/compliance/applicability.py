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
            },
            "pci_dss": {
                "applicable_to": ["fintech", "ecommerce"],
                "controls": ["cardholder_data", "tokenization", "encryption", "access_control", "audit_log", "mfa"],
                "priority": "CRITICAL"
            },
            "hipaa": {
                "applicable_to": ["healthcare"],
                "controls": ["access_control", "encryption", "audit_log", "breach_notification"],
                "priority": "CRITICAL"
            },
            "owasp_top10": {
                "applicable_to": ["any"],
                "controls": ["waf", "auth", "injection", "xss", "ssrf", "rce"],
                "priority": "HIGH"
            },
            "mitre_atlas": {
                "applicable_to": ["ai", "ml"],
                "controls": ["model_access", "data_poisoning", "output_manipulation", "execution_agency"],
                "priority": "HIGH"
            }
        }

    def determine_applicability(self, customer_type: str, industry: str, data_type: str, region: str) -> Dict:
        applicable = []
        for framework_id, config in self.frameworks.items():
            applicable_to = config.get("applicable_to", [])
            if "any" in applicable_to:
                applicable.append({"framework": framework_id, "reason": "Applies to all customers"})
            elif customer_type in applicable_to:
                applicable.append({"framework": framework_id, "reason": f"Applies to {customer_type} customers"})
            elif industry in applicable_to:
                applicable.append({"framework": framework_id, "reason": f"Applies to {industry} industry"})
            elif data_type in applicable_to:
                applicable.append({"framework": framework_id, "reason": f"Applies to {data_type} data"})
        return {
            "customer_type": customer_type,
            "industry": industry,
            "data_type": data_type,
            "region": region,
            "applicable_frameworks": applicable,
            "total_frameworks": len(applicable)
        }

applicability = ApplicabilityEngine()
