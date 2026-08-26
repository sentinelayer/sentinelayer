import json
import hashlib
import os
from datetime import datetime
from typing import Dict, List
import logging

logger = logging.getLogger("sentinelayer.evidence")

class EvidenceCollector:
    def __init__(self):
        self.evidence_dir = "private/evidence"
        os.makedirs(self.evidence_dir, exist_ok=True)
        self.collected = []
    
    def collect(self, evidence_type: str, data: Dict, source: str) -> Dict:
        evidence = {
            "id": hashlib.sha256(json.dumps(data).encode()).hexdigest()[:16],
            "type": evidence_type,
            "data": data,
            "source": source,
            "timestamp": datetime.utcnow().isoformat(),
            "integrity": self._calculate_integrity(data)
        }
        
        self.collected.append(evidence)
        self._persist(evidence)
        
        return evidence
    
    def _calculate_integrity(self, data: Dict) -> str:
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    
    def _persist(self, evidence: Dict):
        path = f"{self.evidence_dir}/{evidence['id']}.json"
        with open(path, "w") as f:
            json.dump(evidence, f, indent=2)
        logger.info(f"Evidence persisted: {path}")
    
    def verify(self, evidence_id: str) -> bool:
        path = f"{self.evidence_dir}/{evidence_id}.json"
        if not os.path.exists(path):
            return False
        
        with open(path, "r") as f:
            evidence = json.load(f)
        
        expected = self._calculate_integrity(evidence["data"])
        return expected == evidence["integrity"]
    
    def get_evidence(self, evidence_type: str = None) -> List[Dict]:
        if evidence_type:
            return [e for e in self.collected if e["type"] == evidence_type]
        return self.collected
    
    def generate_report(self) -> Dict:
        return {
            "total_evidence": len(self.collected),
            "by_type": self._group_by_type(),
            "integrity_verified": sum(1 for e in self.collected if self.verify(e["id"])),
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _group_by_type(self) -> Dict:
        groups = {}
        for e in self.collected:
            groups[e["type"]] = groups.get(e["type"], 0) + 1
        return groups

evidence_collector = EvidenceCollector()
