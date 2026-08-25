from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

@dataclass
class Tenant:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    is_active: bool = True
    settings: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Application:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    name: str = ""
    description: str = ""
    endpoints: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    is_active: bool = True

@dataclass
class Policy:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    name: str = ""
    description: str = ""
    type: str = "waf"
    rules: List[Dict[str, Any]] = field(default_factory=list)
    enabled: bool = True
    priority: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class Incident:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    request_id: str = ""
    severity: str = "low"
    type: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    resolved_at: Optional[str] = None
    status: str = "open"

class ControlPlane:
    def __init__(self):
        self.tenants: Dict[str, Tenant] = {}
        self.applications: Dict[str, Application] = {}
        self.policies: Dict[str, Policy] = {}
        self.incidents: List[Incident] = []
    
    def create_tenant(self, name: str, description: str = "") -> Tenant:
        tenant = Tenant(name=name, description=description)
        self.tenants[tenant.id] = tenant
        return tenant
    
    def list_tenants(self) -> List[Tenant]:
        return list(self.tenants.values())
    
    def create_application(self, tenant_id: str, name: str) -> Optional[Application]:
        if tenant_id not in self.tenants:
            return None
        app = Application(tenant_id=tenant_id, name=name)
        self.applications[app.id] = app
        return app
    
    def create_policy(self, tenant_id: str, name: str, policy_type: str) -> Optional[Policy]:
        if tenant_id not in self.tenants:
            return None
        policy = Policy(tenant_id=tenant_id, name=name, type=policy_type)
        self.policies[policy.id] = policy
        return policy
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "tenants": len(self.tenants),
            "applications": len(self.applications),
            "policies": len(self.policies),
            "incidents": len(self.incidents)
        }

_control_plane = None

def get_control_plane():
    global _control_plane
    if _control_plane is None:
        _control_plane = ControlPlane()
    return _control_plane
