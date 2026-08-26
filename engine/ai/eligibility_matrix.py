class AIEligibilityMatrix:
    def __init__(self):
        self.rules = {
            "public": {"can_enter_ai": True, "retention": "standard"},
            "internal": {"can_enter_ai": True, "retention": "limited"},
            "confidential": {"can_enter_ai": False, "retention": "restricted"},
            "restricted": {"can_enter_ai": False, "retention": "none"},
        }

    def can_enter_ai(self, data_classification: str) -> bool:
        return self.rules.get(data_classification, {}).get("can_enter_ai", False)

    def get_retention_policy(self, data_classification: str) -> str:
        return self.rules.get(data_classification, {}).get("retention", "standard")

    def check_eligibility(self, data_classification: str, purpose: str) -> dict:
        return {
            "eligible": self.can_enter_ai(data_classification),
            "retention": self.get_retention_policy(data_classification),
            "purpose": purpose,
        }
