from datetime import datetime, timedelta
from typing import Dict, List
from src.sentinelayer.evidence.matrix import evidence_matrix

class EvidenceLifecycle:
    def __init__(self):
        self.matrix = evidence_matrix

    def list_evidence(self, requirement_id: str = None) -> List[Dict]:
        return self.matrix.get_matrix(requirement_id)

    def save_evidence(self, requirement_id: str, control_id: str, artifact: str, status: str) -> Dict:
        return self.matrix.add_evidence(requirement_id, control_id, artifact, status)

    def verify_evidence(self, evidence_id: str) -> Dict:
        return self.matrix.verify_evidence(evidence_id)

    def get_compliance_summary(self) -> Dict:
        return self.matrix.get_compliance_summary()

evidence_lifecycle = EvidenceLifecycle()
