import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path


class Provenance:
    def __init__(self, manifest_path: str | None = None):
        self.manifest_path = Path(manifest_path or os.getenv("PROVENANCE_MANIFEST", "security/manifests/runtime-provenance.json"))
        self.verified = False
        self.verified_at: str | None = None

    def verify(self) -> dict[str, object]:
        manifest_path = self.manifest_path
        if not manifest_path.is_absolute():
            manifest_path = Path.cwd() / manifest_path
        if not manifest_path.exists():
            return {"verified": False, "reason": "Manifest not found"}

        try:
            manifest = json.loads(manifest_path.read_text())
            artifacts = manifest.get("artifacts", {})
            if not artifacts:
                return {"verified": False, "reason": "No artifacts in manifest"}

            for path, data in artifacts.items():
                expected_hash = str(data.get("hash", ""))
                if len(expected_hash) != 64 or expected_hash == "placeholder":
                    return {"verified": False, "reason": f"Invalid artifact hash for {path}"}
                artifact_path = Path(path)
                if not artifact_path.is_absolute():
                    artifact_path = Path.cwd() / artifact_path
                if not artifact_path.exists():
                    return {"verified": False, "reason": f"Artifact not found: {path}"}
                actual_hash = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
                if actual_hash != expected_hash:
                    return {"verified": False, "reason": f"Hash mismatch for {path}"}

            self.verified = True
            self.verified_at = datetime.now(UTC).isoformat()
            return {"verified": True, "verified_at": self.verified_at}
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            return {"verified": False, "reason": str(exc)}

    def verify_container(self, container_id: str, expected_hash: str) -> dict[str, object]:
        """Verify deployment-provided runtime digest; never hash a container ID as a substitute."""
        running_hash = os.getenv("SL_RUNNING_ARTIFACT_HASH", "")
        if running_hash and running_hash == expected_hash and len(expected_hash) == 64:
            return {"verified": True, "container_id": container_id, "runtime_hash": running_hash}
        return {"verified": False, "reason": "Runtime artifact digest unavailable or mismatched"}


provenance = Provenance()
