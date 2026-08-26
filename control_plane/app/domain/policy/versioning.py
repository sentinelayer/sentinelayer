class PolicyVersioning:
    def __init__(self):
        self.versions = {}

    def create_version(self, policy_id: str, rules: dict) -> dict:
        if policy_id not in self.versions:
            self.versions[policy_id] = []
        version = len(self.versions[policy_id]) + 1
        entry = {"version": version, "rules": rules, "created_at": "now"}
        self.versions[policy_id].append(entry)
        return entry

    def get_version(self, policy_id: str, version: int) -> dict:
        versions = self.versions.get(policy_id, [])
        if version <= len(versions):
            return versions[version - 1]
        return None

    def rollback(self, policy_id: str, version: int) -> dict:
        return self.get_version(policy_id, version)
