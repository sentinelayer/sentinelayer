from datetime import datetime


class PolicyRollback:
    def __init__(self):
        self.policies = {}
        self.versions = {}
        self.integrity_checks = {}

    def create_version(self, policy_id: str, rules: dict) -> dict:
        version = len(self.versions.get(policy_id, [])) + 1
        entry = {
            "version": version,
            "rules": rules,
            "created_at": datetime.utcnow().isoformat(),
            "integrity": self._calculate_integrity(rules)
        }
        if policy_id not in self.versions:
            self.versions[policy_id] = []
        self.versions[policy_id].append(entry)
        self.policies[policy_id] = entry
        return entry

    def rollback(self, policy_id: str, version: int) -> dict | None:
        versions = self.versions.get(policy_id, [])
        if 1 <= version <= len(versions):
            target = versions[version - 1]
            self.policies[policy_id] = target
            return target
        return None

    def get_version(self, policy_id: str, version: int) -> dict | None:
        versions = self.versions.get(policy_id, [])
        if 1 <= version <= len(versions):
            return versions[version - 1]
        return None

    def verify_integrity(self, policy_id: str) -> bool:
        policy = self.policies.get(policy_id)
        if not policy:
            return False
        expected = self._calculate_integrity(policy["rules"])
        return expected == policy["integrity"]

    def _calculate_integrity(self, rules: dict) -> str:
        import hashlib
        import json
        return hashlib.sha256(json.dumps(rules, sort_keys=True).encode()).hexdigest()

    def list_versions(self, policy_id: str) -> list:
        return self.versions.get(policy_id, [])

    def get_current(self, policy_id: str) -> dict | None:
        return self.policies.get(policy_id)
