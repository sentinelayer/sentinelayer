import json
import os
import hashlib
import logging

logger = logging.getLogger("sentinelayer.provenance")

class RuntimeProvenance:
    def __init__(self):
        self.manifest_path = "private/manifest.json"
        self.verified = False
        self._verify()

    def _verify(self):
        if not os.path.exists(self.manifest_path):
            logger.error("Manifest not found")
            self.verified = False
            return

        with open(self.manifest_path, "r") as f:
            manifest = json.load(f)

        artifacts = manifest.get("artifacts", {})
        if not artifacts:
            logger.error("No artifacts in manifest")
            self.verified = False
            return

        all_match = True
        for path, data in artifacts.items():
            if not os.path.exists(path):
                logger.error(f"Artifact {path} not found")
                all_match = False
                continue

            with open(path, "rb") as f:
                actual_hash = hashlib.sha256(f.read()).hexdigest()

            if actual_hash != data.get("hash"):
                logger.error(f"Artifact {path} hash mismatch")
                all_match = False

        self.verified = all_match
        if self.verified:
            logger.info("Provenance verified successfully")
        else:
            logger.error("Provenance verification failed")

provenance = RuntimeProvenance()
