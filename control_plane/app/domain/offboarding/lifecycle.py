class OffboardingLifecycle:
    def start_offboarding(self, customer_id: str):
        return {"status": "offboarding_started", "customer_id": customer_id}

    def complete_offboarding(self, customer_id: str):
        return {"status": "offboarding_completed", "customer_id": customer_id}
