import os
from typing import Dict, List

class BlastRadius:
    def __init__(self):
        self.mode = os.getenv("BLAST_RADIUS_MODE", "single-tenant")
        self.tenants = []
        self.applications = []
        self.canary_percentage = 5

    def add_tenant(self, tenant_id: str, app_ids: List[str]) -> Dict:
        self.tenants.append({"id": tenant_id, "apps": app_ids})
        return {"tenant_id": tenant_id, "apps": app_ids}

    def add_application(self, app_id: str, name: str) -> Dict:
        self.applications.append({"id": app_id, "name": name})
        return {"app_id": app_id, "name": name}

    def deploy_blast(self, app_id: str, version: str) -> Dict:
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
        elif self.mode == "full":
            return {
                "app_id": app_id,
                "version": version,
                "status": "deployed_to_all_tenants"
            }
        return {"error": "Unknown mode"}

    def get_deployment_status(self, app_id: str) -> Dict:
        return {
            "app_id": app_id,
            "mode": self.mode,
            "tenants": len(self.tenants),
            "applications": len(self.applications)
        }

blast_radius = BlastRadius()
