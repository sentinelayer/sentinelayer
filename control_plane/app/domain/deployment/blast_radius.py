class BlastRadius:
    def __init__(self):
        self.mode = "single-tenant"
        self.canary_percentage = 5

    def deploy(self, app_id: str, version: str):
        if self.mode == "canary":
            return {
                "app_id": app_id,
                "version": version,
                "canary_percentage": self.canary_percentage,
                "status": "canary_deployed"
            }
        elif self.mode == "single-tenant":
            return {
                "app_id": app_id,
                "version": version,
                "status": "deployed_to_single_tenant"
            }
        else:
            return {
                "app_id": app_id,
                "version": version,
                "status": "deployed_to_all_tenants"
            }

    def get_status(self):
        return {"mode": self.mode, "canary_percentage": self.canary_percentage}
