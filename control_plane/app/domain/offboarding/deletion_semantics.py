class DeletionSemantics:
    def soft_delete(self, customer_id: str):
        return {"status": "soft_deleted", "customer_id": customer_id}

    def hard_delete(self, customer_id: str):
        return {"status": "hard_deleted", "customer_id": customer_id}
