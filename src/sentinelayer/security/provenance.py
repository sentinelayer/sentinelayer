import hashlib
import os
import json
import time
from typing import Dict, Any, Optional

class RuntimeProvenance:
    def __init__(self):
        self.manifest_file = "private/manifest.json"
        self.manifest = self.load_manifest()
    
    def load_manifest(self) -> Dict[str, Any]:
        try:
            with open(self.manifest_file, "r") as f:
                return json.load(f)
        except:
            return {"artifacts": {}, "timestamp": 0}
    
    def calculate_hash(self, filepath: str) -> str:
        if not os.path.exists(filepath):
            return ""
        with open(filepath, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    
    def verify_artifact(self, artifact_path: str, artifact_id: str) -> bool:
        current_hash = self.calculate_hash(artifact_path)
        stored_hash = self.manifest.get("artifacts", {}).get(artifact_id, {})
        return current_hash == stored_hash.get("hash", "")
    
    def record_artifact(self, artifact_id: str, artifact_path: str, version: str) -> None:
        current_hash = self.calculate_hash(artifact_path)
        self.manifest["artifacts"][artifact_id] = {
            "hash": current_hash,
            "version": version,
            "timestamp": time.time()
        }
        self.save_manifest()
    
    def save_manifest(self):
        os.makedirs("private", exist_ok=True)
        with open(self.manifest_file, "w") as f:
            json.dump(self.manifest, f, indent=2)

def get_provenance() -> RuntimeProvenance:
    return RuntimeProvenance()
