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
    quotas: Dict[str, int] = field(default_factory=dict)  # {"requests_per_min": 1000, "concurrent": 100}

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
    config: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Policy:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    name: str = ""
    description: str = ""
    type: str = "waf"  # waf, rate_limit, behavior, risk
    rules: List[Dict[str, Any]] = field(default_factory=list)
    enabled: bool = True
    priority: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    applied_to: List[str] = field(default_factory=list)  # list of application IDs

@dataclass
class Incident:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    request_id: str = ""
    severity: str = "low"  # low, medium, high, critical
    type: str = ""  # waf_block, anomaly, rate_limit, etc.
    details: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    resolved_at: Optional[str] = None
    status: str = "open"  # open, investigating, resolved

class ControlPlane:
    """Manage tenants, applications, and policies"""
    
    def __init__(self):
        self.tenants: Dict[str, Tenant] = {}
        self.applications: Dict[str, Application] = {}
        self.policies: Dict[str, Policy] = {}
        self.incidents: List[Incident] = []
    
    # ============ TENANT CRUD ============
    def create_tenant(self, name: str, description: str = "", settings: Dict[str, Any] = None) -> Tenant:
        tenant = Tenant(name=name, description=description, settings=settings or {})
        self.tenants[tenant.id] = tenant
        return tenant
    
    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        return self.tenants.get(tenant_id)
    
    def list_tenants(self) -> List[Tenant]:
        return list(self.tenants.values())
    
    def update_tenant(self, tenant_id: str, **kwargs) -> Optional[Tenant]:
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return None
        for key, value in kwargs.items():
            if hasattr(tenant, key):
                setattr(tenant, key, value)
        tenant.updated_at = datetime.now().isoformat()
        return tenant
    
    def delete_tenant(self, tenant_id: str) -> bool:
        if tenant_id in self.tenants:
            del self.tenants[tenant_id]
            return True
        return False
    
    # ============ APPLICATION CRUD ============
    def create_application(self, tenant_id: str, name: str, description: str = "", endpoints: List[str] = None) -> Optional[Application]:
        if tenant_id not in self.tenants:
            return None
        app = Application(
            tenant_id=tenant_id,
            name=name,
            description=description,
            endpoints=endpoints or []
        )
        self.applications[app.id] = app
        return app
    
    def get_application(self, app_id: str) -> Optional[Application]:
        return self.applications.get(app_id)
    
    def list_applications(self, tenant_id: Optional[str] = None) -> List[Application]:
        if tenant_id:
            return [app for app in self.applications.values() if app.tenant_id == tenant_id]
        return list(self.applications.values())
    
    def update_application(self, app_id: str, **kwargs) -> Optional[Application]:
        app = self.applications.get(app_id)
        if not app:
            return None
        for key, value in kwargs.items():
            if hasattr(app, key):
                setattr(app, key, value)
        app.updated_at = datetime.now().isoformat()
        return app
    
    def delete_application(self, app_id: str) -> bool:
        if app_id in self.applications:
            del self.applications[app_id]
            return True
        return False
    
    # ============ POLICY CRUD ============
    def create_policy(self, tenant_id: str, name: str, policy_type: str, rules: List[Dict[str, Any]] = None) -> Optional[Policy]:
        if tenant_id not in self.tenants:
            return None
        policy = Policy(
            tenant_id=tenant_id,
            name=name,
            type=policy_type,
            rules=rules or []
        )
        self.policies[policy.id] = policy
        return policy
    
    def get_policy(self, policy_id: str) -> Optional[Policy]:
        return self.policies.get(policy_id)
    
    def list_policies(self, tenant_id: Optional[str] = None) -> List[Policy]:
        if tenant_id:
            return [p for p in self.policies.values() if p.tenant_id == tenant_id]
        return list(self.policies.values())
    
    def update_policy(self, policy_id: str, **kwargs) -> Optional[Policy]:
        policy = self.policies.get(policy_id)
        if not policy:
            return None
        for key, value in kwargs.items():
            if hasattr(policy, key):
                setattr(policy, key, value)
        policy.updated_at = datetime.now().isoformat()
        return policy
    
    def delete_policy(self, policy_id: str) -> bool:
        if policy_id in self.policies:
            del self.policies[policy_id]
            return True
        return False
    
    # ============ INCIDENT MANAGEMENT ============
    def create_incident(self, tenant_id: str, request_id: str, severity: str, incident_type: str, details: Dict[str, Any] = None) -> Incident:
        incident = Incident(
            tenant_id=tenant_id,
            request_id=request_id,
            severity=severity,
            type=incident_type,
            details=details or {}
        )
        self.incidents.append(incident)
        return incident
    
    def list_incidents(self, tenant_id: Optional[str] = None, status: Optional[str] = None) -> List[Incident]:
        result = self.incidents
        if tenant_id:
            result = [i for i in result if i.tenant_id == tenant_id]
        if status:
            result = [i for i in result if i.status == status]
        return result
    
    def resolve_incident(self, incident_id: str) -> bool:
        for incident in self.incidents:
            if incident.id == incident_id:
                incident.status = "resolved"
                incident.resolved_at = datetime.now().isoformat()
                return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "tenants": len(self.tenants),
            "applications": len(self.applications),
            "policies": len(self.policies),
            "incidents": len(self.incidents),
            "open_incidents": len([i for i in self.incidents if i.status == "open"])
        }

def get_control_plane() -> ControlPlane:
    return ControlPlane()
_control_plane = None

def get_control_plane():
    global _control_plane
    if _control_plane is None:
        _control_plane = ControlPlane()
    return _control_plane
