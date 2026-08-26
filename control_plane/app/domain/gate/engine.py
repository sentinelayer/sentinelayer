class GateEngine:
    def __init__(self):
        self.requirements = {}

    def evaluate(self, requirement_id: str) -> dict:
        req = self.requirements.get(requirement_id)
        if not req:
            return {"status": "REJECTED", "reason": "Requirement not found"}
        checks = []
        results = []
        if req.get("implemented", False):
            checks.append({"name": "Implementation", "status": "PASS"})
            results.append(True)
        else:
            checks.append({"name": "Implementation", "status": "FAIL"})
            results.append(False)
        all_pass = all(results)
        return {"requirement_id": requirement_id, "status": "ACCEPTED" if all_pass else "REJECTED", "checks": checks}
