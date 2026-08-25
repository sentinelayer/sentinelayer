import logging
from typing import Optional, List, Tuple
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)

@dataclass
class Resource:
    type: str
    id: str
    tenant_id: str
    owner_id: Optional[str] = None

class AuthorizationMiddleware:
    def __init__(self):
        self.resource_patterns = {
            r"^/api/v1/orders/([^/]+)$": ("order", 1),
            r"^/api/v1/users/([^/]+)$": ("user", 1),
            r"^/api/v1/payments/([^/]+)$": ("payment", 1),
        }
        self.admin_override_alerts = []
    
    def extract_resource_from_path(self, path: str):
        for pattern, (resource_type, id_group) in self.resource_patterns.items():
            match = re.match(pattern, path)
            if match:
                return (resource_type, match.group(id_group))
        return None
    
    def _alert_admin_override(self, user_id: str, resource_id: str, reason: str):
        """Log admin override untuk audit"""
        alert = {
            "type": "admin_override",
            "user_id": user_id,
            "resource_id": resource_id,
            "reason": reason,
            "timestamp": time.time()
        }
        self.admin_override_alerts.append(alert)
        logger.warning(f"🔴 ADMIN OVERRIDE: user={user_id}, resource={resource_id}, reason={reason}")
        
        # Keep only last 100
        if len(self.admin_override_alerts) > 100:
            self.admin_override_alerts.pop(0)
    
    def check_access(self, resource_tenant_id: str, resource_owner_id: str, 
                     user_tenant_id: str, user_id: str, user_roles: list = None) -> Tuple[bool, str]:
        # Admin override with alert
        if user_roles and "admin" in user_roles:
            self._alert_admin_override(user_id, resource_owner_id, "Admin override triggered")
            return True, "Admin override"
        
        if resource_tenant_id != user_tenant_id:
            return False, "Tenant mismatch"
        
        if resource_owner_id and resource_owner_id != user_id:
            return False, "Resource belongs to another user"
        
        return True, "Access granted"
    
    def validate_request(self, resource: Resource, user_tenant_id: str, user_id: str, user_roles: list = None) -> Tuple[bool, str]:
        return self.check_access(
            resource_tenant_id=resource.tenant_id,
            resource_owner_id=resource.owner_id,
            user_tenant_id=user_tenant_id,
            user_id=user_id,
            user_roles=user_roles
        )
    
    def get_admin_override_alerts(self) -> list:
        return self.admin_override_alerts

def get_authorization_middleware() -> AuthorizationMiddleware:
    return AuthorizationMiddleware()
