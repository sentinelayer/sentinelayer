class BlastRadius:
    def __init__(self):
        self.mode = "single-tenant"

    def deploy(self, app_id: str):
        return {"app_id": app_id, "mode": self.mode, "status": "deployed"}
