import hashlib
import os
import json
import time
import logging

logger = logging.getLogger(__name__)

class RuntimeProvenance:
    def __init__(self):
        self.manifest_file = "private/manifest.json"
        self.manifest = self.load_manifest()
        self.verified = False
        self.verify_on_startup()
    
    def load_manifest(self) -> dict:
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
    
    def verify_on_startup(self):
        logger.info("Verifying runtime provenance...")
        artifacts = self.manifest.get("artifacts", {})
        if not artifacts:
            logger.warning("No artifacts in manifest, skipping verification")
            self.verified = True
            return
        
        all_verified = True
        for artifact_id, data in artifacts.items():
            artifact_path = data.get("path", "")
            stored_hash = data.get("hash", "")
            if not os.path.exists(artifact_path):
                logger.error(f"Artifact {artifact_id} not found: {artifact_path}")
                all_verified = False
                continue
            current_hash = self.calculate_hash(artifact_path)
            if current_hash != stored_hash:
                logger.error(f"Artifact {artifact_id} hash mismatch!")
                all_verified = False
            else:
                logger.info(f"Artifact {artifact_id} verified")
        
        self.verified = all_verified
        if not self.verified:
            logger.critical("Runtime provenance verification FAILED!")
        else:
            logger.info("All artifacts verified")
    
    def get_status(self) -> dict:
        return {
            "verified": self.verified,
            "artifacts_count": len(self.manifest.get("artifacts", {})),
            "timestamp": self.manifest.get("timestamp", 0)
        }

_provenance = None

def get_provenance():
    global _provenance
    if _provenance is None:
        _provenance = RuntimeProvenance()
    return _provenance
