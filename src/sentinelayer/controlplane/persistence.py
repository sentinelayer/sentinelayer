import json
import os
from typing import List, Optional
from .models import Tenant, Application, Policy, Incident

class ControlPlanePersistence:
    def __init__(self, data_dir: str = "private/controlplane"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.tenants_file = os.path.join(data_dir, "tenants.json")
        self.apps_file = os.path.join(data_dir, "applications.json")
        self.policies_file = os.path.join(data_dir, "policies.json")
        self.incidents_file = os.path.join(data_dir, "incidents.json")
    
    def _load(self, filepath: str) -> list:
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                return json.load(f)
        return []
    
    def _save(self, filepath: str, data: list):
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)
    
    def load_tenants(self) -> List[Tenant]:
        return [Tenant(**t) for t in self._load(self.tenants_file)]
    
    def save_tenants(self, tenants: List[Tenant]):
        self._save(self.tenants_file, [t.__dict__ for t in tenants])
    
    def load_applications(self) -> List[Application]:
        return [Application(**a) for a in self._load(self.apps_file)]
    
    def save_applications(self, apps: List[Application]):
        self._save(self.apps_file, [a.__dict__ for a in apps])
    
    def load_policies(self) -> List[Policy]:
        return [Policy(**p) for p in self._load(self.policies_file)]
    
    def save_policies(self, policies: List[Policy]):
        self._save(self.policies_file, [p.__dict__ for p in policies])
    
    def load_incidents(self) -> List[Incident]:
        return [Incident(**i) for i in self._load(self.incidents_file)]
    
    def save_incidents(self, incidents: List[Incident]):
        self._save(self.incidents_file, [i.__dict__ for i in incidents])
