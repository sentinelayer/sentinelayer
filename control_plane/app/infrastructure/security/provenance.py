import hashlib
import json
import os
from typing import Dict

class Provenance:
    def __init__(self):
        self.manifest_path = "security/manifests/runtime-provenance.json"
        self.verified = False

    def verify(self) -> Dict:
        if not os.path.exists(self.manifest_path):
            return {"verified": False, "reason": "Manifest not found"}
        try:
            with open(self.manifest_path, "r") as f:
                manifest = json.load(f)
            artifacts = manifest.get("artifacts", {})
            for path, data in artifacts.items():
                if os.path.exists(path):
                    with open(path, "rb") as f:
                        actual_hash = hashlib.sha256(f.read()).hexdigest()
                    if actual_hash != data.get("hash"):
                        return {"verified": False, "reason": f"Hash mismatch for {path}"}
            self.verified = True
            return {"verified": True}
        except Exception as e:
            return {"verified": False, "reason": str(e)}
