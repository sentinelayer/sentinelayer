import hashlib
import os
import json
import time
import sys
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class RuntimeProvenance:
    def __init__(self):
        self.manifest_file = "private/manifest.json"
        self.manifest = self.load_manifest()
        self.verified = False
        self.verify_on_startup()
    
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
    
    def verify_on_startup(self):
        """Hook ke startup - verifikasi semua artifact"""
        logger.info("🔍 Verifying runtime provenance...")
        
        artifacts = self.manifest.get("artifacts", {})
        if not artifacts:
            logger.warning("⚠️ No artifacts in manifest, skipping verification")
            self.verified = True
            return
        
        all_verified = True
        for artifact_id, data in artifacts.items():
            artifact_path = data.get("path", "")
            stored_hash = data.get("hash", "")
            
            if not artifact_path or not os.path.exists(artifact_path):
                logger.error(f"❌ Artifact {artifact_id} not found: {artifact_path}")
                all_verified = False
                continue
            
            current_hash = self.calculate_hash(artifact_path)
            if current_hash != stored_hash:
                logger.error(f"❌ Artifact {artifact_id} hash mismatch!")
                logger.error(f"   Expected: {stored_hash}")
                logger.error(f"   Actual:   {current_hash}")
                all_verified = False
            else:
                logger.info(f"✅ Artifact {artifact_id} verified")
        
        self.verified = all_verified
        
        if not self.verified:
            logger.critical("❌ Runtime provenance verification FAILED!")
            logger.critical("   Artifacts do not match approved manifest.")
            logger.critical("   Application may be compromised.")
            # Di production, bisa exit
            # if os.getenv("ENVIRONMENT") == "production":
            #     sys.exit(1)
        else:
            logger.info("✅ All artifacts verified")
    
    def verify_artifact(self, artifact_path: str, artifact_id: str) -> bool:
        current_hash = self.calculate_hash(artifact_path)
        stored_hash = self.manifest.get("artifacts", {}).get(artifact_id, {}).get("hash", "")
        return current_hash == stored_hash
    
    def record_artifact(self, artifact_id: str, artifact_path: str, version: str) -> None:
        current_hash = self.calculate_hash(artifact_path)
        self.manifest["artifacts"][artifact_id] = {
            "hash": current_hash,
            "version": version,
            "timestamp": time.time(),
            "path": artifact_path
        }
        self.save_manifest()
        logger.info(f"✅ Artifact {artifact_id} recorded")
    
    def save_manifest(self):
        os.makedirs("private", exist_ok=True)
        with open(self.manifest_file, "w") as f:
            json.dump(self.manifest, f, indent=2)
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "verified": self.verified,
            "artifacts_count": len(self.manifest.get("artifacts", {})),
            "timestamp": self.manifest.get("timestamp", 0)
        }

def get_provenance() -> RuntimeProvenance:
    return RuntimeProvenance()
