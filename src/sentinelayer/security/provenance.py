import json
import os
from pathlib import Path

class RuntimeProvenance:
    def __init__(self):
        self.manifest_path = "private/manifest.json"
        self.verified = False
        self.verify_manifest()
    
    def verify_manifest(self):
        if not os.path.exists(self.manifest_path):
            self.verified = False
            raise RuntimeError("Manifest not found - runtime provenance failed")
        
        with open(self.manifest_path, "r") as f:
            manifest = json.load(f)
        
        if not manifest.get("artifacts"):
            self.verified = False
            raise RuntimeError("Empty manifest - runtime provenance failed")
        
        # Verify artifact signatures
        for artifact, data in manifest["artifacts"].items():
            if not data.get("verified", False):
                self.verified = False
                raise RuntimeError(f"Artifact {artifact} not verified")
        
        self.verified = True
    
    def verify_current_artifact(self, artifact_path: str):
        if not self.verified:
            raise RuntimeError("Runtime provenance not verified")
        
        # Compare hash
        import hashlib
        with open(artifact_path, "rb") as f:
            current_hash = hashlib.sha256(f.read()).hexdigest()
        
        with open(self.manifest_path, "r") as f:
            manifest = json.load(f)
        
        expected_hash = manifest["artifacts"].get(artifact_path, {}).get("hash")
        if not expected_hash or current_hash != expected_hash:
            raise RuntimeError(f"Artifact {artifact_path} does not match manifest")
        
        return True

provenance = RuntimeProvenance()
