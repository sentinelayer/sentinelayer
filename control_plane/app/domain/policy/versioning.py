import json
from datetime import datetime
from typing import Dict, Optional

class PolicyVersioning:
    def __init__(self):
        self.versions = {}

    def create_version(self, policy_id: str, rules: Dict) -> Dict:
        if policy_id not in self.versions:
            self.versions[policy_id] = []
        version = len(self.versions[policy_id]) + 1
        entry = {
            "version": version,
            "rules": rules,
            "created_at": datetime.utcnow().isoformat()
        }
        self.versions[policy_id].append(entry)
        return entry

    def get_version(self, policy_id: str, version: int) -> Optional[Dict]:
        versions = self.versions.get(policy_id, [])
        if 1 <= version <= len(versions):
            return versions[version - 1]
        return None

    def rollback(self, policy_id: str, version: int) -> Optional[Dict]:
        return self.get_version(policy_id, version)

    def list_versions(self, policy_id: str) -> list:
        return self.versions.get(policy_id, [])
