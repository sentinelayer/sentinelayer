from datetime import datetime, timedelta
from typing import Dict, List
import json

class ComplianceReporter:
    def __init__(self):
        self.standards = {
            "soc2": {
                "controls": ["access_control", "audit_log", "encryption", "backup", "incident_response"],
                "required": True
            },
            "iso27001": {
                "controls": ["access_control", "audit_log", "encryption", "backup", "incident_response", "training"],
                "required": True
            },
            "gdpr": {
                "controls": ["data_classification", "retention", "deletion", "consent", "breach_notification"],
                "required": True
            }
        }
    
    def generate_report(self, standard: str, evidence: List[Dict]) -> Dict:
        if standard not in self.standards:
            return {"error": f"Standard {standard} not found"}
        
        controls = self.standards[standard]["controls"]
        status = {}
        
        for control in controls:
            evidence_items = [e for e in evidence if e.get("type") == control]
            status[control] = {
                "status": "compliant" if evidence_items else "non_compliant",
                "evidence_count": len(evidence_items),
                "evidence": evidence_items[:5]
            }
        
        compliant_count = sum(1 for s in status.values() if s["status"] == "compliant")
        total_count = len(status)
        
        return {
            "standard": standard,
            "summary": {
                "compliant": compliant_count,
                "non_compliant": total_count - compliant_count,
                "total": total_count,
                "compliance_percentage": (compliant_count / total_count) * 100 if total_count > 0 else 0
            },
            "controls": status,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def get_all_standards(self) -> List[str]:
        return list(self.standards.keys())

compliance_reporter = ComplianceReporter()
