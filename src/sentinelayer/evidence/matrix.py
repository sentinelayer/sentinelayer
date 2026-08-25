import json
import hashlib
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import os

@dataclass
class Evidence:
    evidence_id: str
    requirement_id: str
    control_id: str
    artifact: str
    timestamp: float
    hash: str
    owner: str
    reviewer: str
    retention: int  # days
    validity: int   # days
    chain_of_custody: List[Dict[str, Any]] = field(default_factory=list)
    implementation_version: str = "0.1.0"
    status: str = "CREATED"  # CREATED, VERIFIED, VALID, EXPIRED, REVOKED

class EvidenceMatrix:
    """Automated evidence collection and management"""
    
    def __init__(self):
        self.evidences: Dict[str, Evidence] = {}
        self.evidence_dir = "private/evidence/requirements"
        os.makedirs(self.evidence_dir, exist_ok=True)
        self.load_evidence()
    
    def create_evidence(
        self,
        requirement_id: str,
        control_id: str,
        artifact: str,
        owner: str = "founder"
    ) -> Evidence:
        """Create a new evidence entry"""
        evidence_id = f"EV-{len(self.evidences) + 1:03d}"
        
        # Generate hash
        content = f"{requirement_id}:{control_id}:{artifact}:{time.time()}"
        hash_val = hashlib.sha256(open(artifact, "rb").read()).hexdigest()
        
        evidence = Evidence(
            evidence_id=evidence_id,
            requirement_id=requirement_id,
            control_id=control_id,
            artifact=artifact,
            timestamp=time.time(),
            hash=hash_val,
            owner=owner,
            reviewer="PENDING",
            retention=365,  # 1 year
            validity=90,    # 3 months
            chain_of_custody=[{
                "action": "CREATED",
                "timestamp": time.time(),
                "owner": owner
            }]
        )
        
        self.evidences[evidence_id] = evidence
        self.save_evidence(evidence)
        return evidence
    
    def verify_evidence(self, evidence_id: str, reviewer: str) -> bool:
        """Verify evidence by reviewer"""
        evidence = self.evidences.get(evidence_id)
        if not evidence:
            return False
        
        evidence.reviewer = reviewer
        evidence.status = "VERIFIED"
        evidence.chain_of_custody.append({
            "action": "VERIFIED",
            "timestamp": time.time(),
            "reviewer": reviewer
        })
        
        self.save_evidence(evidence)
        return True
    
    def validate_evidence(self, evidence_id: str) -> bool:
        if time.time() - evidence.timestamp > evidence.validity * 86400:
            evidence.status = "EXPIRED"
            self.save_evidence(evidence)
            return False
        """Validate evidence and check expiration"""
        evidence = self.evidences.get(evidence_id)
        if not evidence:
            return False
        
        # Check if expired
        age = time.time() - evidence.timestamp
        if age > evidence.validity * 86400:
            evidence.status = "EXPIRED"
            return False
        
        evidence.status = "VALID"
        self.save_evidence(evidence)
        return True
    
    def revoke_evidence(self, evidence_id: str, reason: str) -> bool:
        """Revoke evidence"""
        evidence = self.evidences.get(evidence_id)
        if not evidence:
            return False
        
        evidence.status = "REVOKED"
        evidence.chain_of_custody.append({
            "action": "REVOKED",
            "timestamp": time.time(),
            "reason": reason
        })
        
        self.save_evidence(evidence)
        return True
    
    def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        return self.evidences.get(evidence_id)
    
    def list_evidence(self, status: Optional[str] = None) -> List[Evidence]:
        result = list(self.evidences.values())
        if status:
            result = [e for e in result if e.status == status]
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        total = len(self.evidences)
        if total == 0:
            return {"total": 0}
        
        status_counts = {}
        for evidence in self.evidences.values():
            status_counts[evidence.status] = status_counts.get(evidence.status, 0) + 1
        
        return {
            "total": total,
            "status_counts": status_counts,
            "valid_count": status_counts.get("VALID", 0),
            "expired_count": status_counts.get("EXPIRED", 0),
            "revoked_count": status_counts.get("REVOKED", 0),
            "pending_verification": status_counts.get("CREATED", 0)
        }
    
    def save_evidence(self, evidence: Evidence):
        """Save evidence to file"""
        filepath = f"{self.evidence_dir}/{evidence.evidence_id}.json"
        data = {
            "evidence_id": evidence.evidence_id,
            "requirement_id": evidence.requirement_id,
            "control_id": evidence.control_id,
            "artifact": evidence.artifact,
            "timestamp": evidence.timestamp,
            "hash": evidence.hash,
            "owner": evidence.owner,
            "reviewer": evidence.reviewer,
            "retention": evidence.retention,
            "validity": evidence.validity,
            "chain_of_custody": evidence.chain_of_custody,
            "implementation_version": evidence.implementation_version,
            "status": evidence.status
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    
    def load_evidence(self):
        """Load evidence from files"""
        if not os.path.exists(self.evidence_dir):
            return
        
        for filename in os.listdir(self.evidence_dir):
            if not filename.endswith(".json"):
                continue
            filepath = os.path.join(self.evidence_dir, filename)
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    evidence = Evidence(
                        evidence_id=data["evidence_id"],
                        requirement_id=data["requirement_id"],
                        control_id=data["control_id"],
                        artifact=data["artifact"],
                        timestamp=data["timestamp"],
                        hash=data["hash"],
                        owner=data["owner"],
                        reviewer=data["reviewer"],
                        retention=data["retention"],
                        validity=data["validity"],
                        chain_of_custody=data.get("chain_of_custody", []),
                        implementation_version=data.get("implementation_version", "0.1.0"),
                        status=data.get("status", "CREATED")
                    )
                    self.evidences[evidence.evidence_id] = evidence
            except Exception as e:
                print(f"Error loading evidence {filename}: {e}")

def get_evidence_matrix() -> EvidenceMatrix:
    return EvidenceMatrix()
_evidence_matrix = None

def get_evidence_matrix():
    global _evidence_matrix
    if _evidence_matrix is None:
        _evidence_matrix = EvidenceMatrix()
    return _evidence_matrix
