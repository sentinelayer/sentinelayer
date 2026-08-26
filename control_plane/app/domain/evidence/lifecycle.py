"""
Evidence Lifecycle & Revocation Model (Blueprint Section 0.6)

CREATED → VERIFIED → VALID → SUPERSEDED / EXPIRED / REVOKED

Rules:
- If implementation changes, related evidence automatically EXPIRED.
- Evidence must carry implementation_version.
- If current_version != evidence_version → status = EXPIRED.
- 2026: must include runtime provenance where applicable.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import hashlib
import json


ALLOWED_TRANSITIONS = {
    "CREATED": {"VERIFIED", "REVOKED"},
    "VERIFIED": {"VALID", "EXPIRED", "REVOKED"},
    "VALID": {"SUPERSEDED", "EXPIRED", "REVOKED"},
    "SUPERSEDED": set(),
    "EXPIRED": set(),
    "REVOKED": set(),
}


class EvidenceLifecycle:
    def __init__(self, retention_days: int = 2555) -> None:
        self._store: Dict[str, Dict[str, Any]] = {}
        self.retention_days = retention_days

    def create(
        self,
        evidence_id: str,
        requirement_id: str,
        control_id: str,
        artifact: str,
        owner: str,
        implementation_version: str,
        data: Optional[Dict] = None,
        reviewer: Optional[str] = None,
        relationship: Optional[str] = None,
        related_id: Optional[str] = None,
        runtime_artifact_hash: Optional[str] = None,
        approved_manifest_hash: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = data or {}
        hash_value = hashlib.sha256(
            json.dumps({"artifact": artifact, **payload}, sort_keys=True).encode()
        ).hexdigest()

        entry = {
            "id": evidence_id,
            "requirement_id": requirement_id,
            "control_id": control_id,
            "artifact": artifact,
            "hash_sha256": hash_value,
            "owner": owner,
            "reviewer": reviewer,
            "status": "CREATED",
            "implementation_version": implementation_version,
            "runtime_artifact_hash": runtime_artifact_hash,
            "approved_manifest_hash": approved_manifest_hash,
            "relationship": relationship,
            "related_id": related_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "chain_of_custody": [
                {
                    "action": "CREATED",
                    "actor": owner,
                    "at": datetime.now(timezone.utc).isoformat(),
                }
            ],
            "data": payload,
        }
        self._store[evidence_id] = entry
        return entry

    def _transition(self, evidence_id: str, new_status: str, actor: str, reason: str = "") -> Dict[str, Any]:
        if evidence_id not in self._store:
            return {"error": "Evidence not found"}

        entry = self._store[evidence_id]
        current = entry["status"]
        if new_status not in ALLOWED_TRANSITIONS.get(current, set()):
            return {
                "error": f"Illegal transition {current} → {new_status}",
                "current": current,
            }

        entry["status"] = new_status
        ts = datetime.now(timezone.utc).isoformat()
        entry["chain_of_custody"].append(
            {"action": new_status, "actor": actor, "at": ts, "reason": reason}
        )

        if new_status == "VERIFIED":
            entry["verified_at"] = ts
        elif new_status == "VALID":
            entry["validated_at"] = ts
        elif new_status == "EXPIRED":
            entry["expired_at"] = ts
        elif new_status == "REVOKED":
            entry["revoked_at"] = ts
            entry["revoked_reason"] = reason

        return entry

    def verify(self, evidence_id: str, actor: str) -> Dict[str, Any]:
        entry = self._store.get(evidence_id)
        if not entry:
            return {"error": "Evidence not found"}

        expected = hashlib.sha256(
            json.dumps(
                {"artifact": entry["artifact"], **entry.get("data", {})},
                sort_keys=True,
            ).encode()
        ).hexdigest()
        if expected != entry["hash_sha256"]:
            return {"error": "Hash mismatch — integrity compromised"}

        return self._transition(evidence_id, "VERIFIED", actor)

    def validate(
        self,
        evidence_id: str,
        actor: str,
        current_system_version: str,
    ) -> Dict[str, Any]:
        entry = self._store.get(evidence_id)
        if not entry:
            return {"error": "Evidence not found"}

        if entry["implementation_version"] != current_system_version:
            return self._transition(
                evidence_id,
                "EXPIRED",
                actor="system",
                reason=f"Version drift: evidence={entry['implementation_version']} current={current_system_version}",
            )

        if entry.get("runtime_artifact_hash") and entry.get("approved_manifest_hash"):
            if entry["runtime_artifact_hash"] != entry["approved_manifest_hash"]:
                return self._transition(
                    evidence_id,
                    "REVOKED",
                    actor="system",
                    reason="Runtime provenance mismatch",
                )

        entry["current_system_version"] = current_system_version
        return self._transition(evidence_id, "VALID", actor)

    def expire(self, evidence_id: str, reason: str = "Retention or version change") -> Dict[str, Any]:
        return self._transition(evidence_id, "EXPIRED", actor="system", reason=reason)

    def revoke(self, evidence_id: str, actor: str, reason: str) -> Dict[str, Any]:
        return self._transition(evidence_id, "REVOKED", actor=actor, reason=reason)

    def supersede(self, evidence_id: str, actor: str, new_evidence_id: str) -> Dict[str, Any]:
        return self._transition(
            evidence_id,
            "SUPERSEDED",
            actor=actor,
            reason=f"Superseded by {new_evidence_id}",
        )

    def is_valid(self, evidence_id: str, current_system_version: Optional[str] = None) -> bool:
        entry = self._store.get(evidence_id)
        if not entry:
            return False
        if entry["status"] != "VALID":
            return False
        if current_system_version and entry["implementation_version"] != current_system_version:
            return False
        return True

    def expire_on_version_change(self, old_version: str, new_version: str) -> List[str]:
        expired = []
        for eid, entry in self._store.items():
            if entry["implementation_version"] == old_version and entry["status"] in (
                "VERIFIED",
                "VALID",
            ):
                self.expire(eid, reason=f"Implementation version changed {old_version} → {new_version}")
                expired.append(eid)
        return expired

    def get(self, evidence_id: str) -> Optional[Dict[str, Any]]:
        return self._store.get(evidence_id)

    def get_status(self, evidence_id: str) -> Dict[str, Any]:
        entry = self._store.get(evidence_id)
        if not entry:
            return {"status": "NOT_FOUND"}
        return {"status": entry["status"], "implementation_version": entry["implementation_version"]}
