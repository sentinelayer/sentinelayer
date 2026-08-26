import hashlib
import json
from datetime import datetime


class EvidenceChain:
    def __init__(self):
        self.evidence = {}
        self.chain = {}

    def add_evidence(self, evidence_id: str, artifact: str, data: dict) -> dict:
        hash_value = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

        entry = {
            "id": evidence_id,
            "artifact": artifact,
            "data": data,
            "hash": hash_value,
            "previous_hash": self.chain.get(evidence_id, {}).get("hash") if evidence_id in self.chain else None,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "CREATED"
        }

        self.evidence[evidence_id] = entry
        self.chain[evidence_id] = entry
        return entry

    def verify(self, evidence_id: str) -> bool:
        if evidence_id not in self.evidence:
            return False

        entry = self.evidence[evidence_id]
        expected_hash = hashlib.sha256(json.dumps(entry["data"], sort_keys=True).encode()).hexdigest()
        return expected_hash == entry["hash"]

    def get_chain(self, evidence_id: str) -> dict | None:
        return self.chain.get(evidence_id)

    def get_all(self) -> list:
        return list(self.chain.values())

    def revoke(self, evidence_id: str) -> dict:
        if evidence_id not in self.evidence:
            return {"error": "Evidence not found"}

        self.evidence[evidence_id]["status"] = "REVOKED"
        self.evidence[evidence_id]["revoked_at"] = datetime.utcnow().isoformat()
        return self.evidence[evidence_id]
