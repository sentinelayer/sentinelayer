import hashlib
import json
import os
from typing import Dict

class Provenance:
    def __init__(self):
        self.manifest_path = "security/manifests/runtime-provenance.json"
        self.verified = False
        self.verified_at = None

    def verify(self) -> Dict:
        if not os.path.exists(self.manifest_path):
            return {"verified": False, "reason": "Manifest not found"}

        try:
            with open(self.manifest_path, "r") as f:
                manifest = json.load(f)

            artifacts = manifest.get("artifacts", {})
            if not artifacts:
                return {"verified": False, "reason": "No artifacts in manifest"}

            for path, data in artifacts.items():
                if not os.path.exists(path):
                    return {"verified": False, "reason": f"Artifact not found: {path}"}

                with open(path, "rb") as f:
                    actual_hash = hashlib.sha256(f.read()).hexdigest()

                if actual_hash != data.get("hash"):
                    return {"verified": False, "reason": f"Hash mismatch for {path}"}

            self.verified = True
            self.verified_at = datetime.utcnow().isoformat()
            return {"verified": True}

        except Exception as e:
            return {"verified": False, "reason": str(e)}

    def verify_container(self, container_id: str, expected_hash: str) -> Dict:
        actual_hash = hashlib.sha256(container_id.encode()).hexdigest()
        if actual_hash == expected_hash:
            return {"verified": True, "container_id": container_id}
        return {"verified": False, "reason": "Container hash mismatch"}

provenance = Provenance()
