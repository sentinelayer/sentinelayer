import json
import os
import hashlib

class RuntimeProvenance:
    def __init__(self):
        self.manifest_path = "private/manifest.json"
        self.verified = False
        self._verify()

    def _verify(self):
        if not os.path.exists(self.manifest_path):
            raise RuntimeError("Manifest not found")

        with open(self.manifest_path, "r") as f:
            manifest = json.load(f)

        artifacts = manifest.get("artifacts", {})
        if not artifacts:
            raise RuntimeError("No artifacts in manifest")

        for path, data in artifacts.items():
            if not os.path.exists(path):
                raise RuntimeError(f"Artifact {path} not found")

            with open(path, "rb") as f:
                actual_hash = hashlib.sha256(f.read()).hexdigest()

            if actual_hash != data.get("hash"):
                raise RuntimeError(f"Artifact {path} hash mismatch")

        self.verified = True

provenance = RuntimeProvenance()
