from datetime import datetime
from typing import Dict, List

class ComplianceReporting:
    def __init__(self):
        self.frameworks = {
            "uu_pdp": {
                "controls": ["consent", "retention", "deletion", "access", "breach_notification"],
                "status": "partial"
            },
            "pci_dss": {
                "controls": ["cardholder_data", "tokenization", "encryption", "access_control", "mfa"],
                "status": "partial"
            },
            "iso27001": {
                "controls": ["access_control", "audit_log", "encryption", "backup", "incident_response", "training"],
                "status": "partial"
            }
        }

    def get_status(self, framework: str) -> Dict:
        return self.frameworks.get(framework, {"error": "Framework not found"})

    def generate_report(self, framework: str) -> Dict:
        framework_data = self.get_status(framework)
        if "error" in framework_data:
            return framework_data
        return {
            "framework": framework,
            "status": framework_data["status"],
            "controls": framework_data["controls"],
            "compliant_count": 0,
            "total_controls": len(framework_data["controls"]),
            "generated_at": datetime.utcnow().isoformat()
        }

    def list_frameworks(self) -> List[str]:
        return list(self.frameworks.keys())
