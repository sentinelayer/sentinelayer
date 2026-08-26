import json
import os
import hashlib

class Provenance:
    def __init__(self):
        self.manifest_path = "security/manifests/runtime-provenance.json"
        self.verified = False

    def verify(self):
        if not os.path.exists(self.manifest_path):
            self.verified = False
            return {"verified": False, "reason": "Manifest not found"}
        with open(self.manifest_path, "r") as f:
            manifest = json.load(f)
        artifacts = manifest.get("artifacts", {})
        if not artifacts:
            self.verified = False
            return {"verified": False, "reason": "No artifacts"}
        for path, data in artifacts.items():
            if os.path.exists(path):
                with open(path, "rb") as f:
                    actual_hash = hashlib.sha256(f.read()).hexdigest()
                if actual_hash != data.get("hash"):
                    self.verified = False
                    return {"verified": False, "reason": f"Hash mismatch for {path}"}
        self.verified = True
        return {"verified": True}
