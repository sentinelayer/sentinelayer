class ApplicabilityEngine:
    def __init__(self):
        self.frameworks = {
            "soc2": {"applicable_to": ["enterprise", "saas", "fintech"]},
            "iso27001": {"applicable_to": ["enterprise", "saas", "fintech", "government"]},
            "gdpr": {"applicable_to": ["any"]}
        }

    def determine_applicability(self, customer_type: str):
        applicable = []
        for framework_id, config in self.frameworks.items():
            if "any" in config["applicable_to"] or customer_type in config["applicable_to"]:
                applicable.append(framework_id)
        return {"customer_type": customer_type, "applicable_frameworks": applicable}
