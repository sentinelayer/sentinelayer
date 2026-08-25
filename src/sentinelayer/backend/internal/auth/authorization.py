from typing import Optional, Dict, Any
from dataclasses import dataclass
import re
import logging

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
    
    def extract_resource_from_path(self, path: str):
        for pattern, (resource_type, id_group) in self.resource_patterns.items():
            match = re.match(pattern, path)
            if match:
                return (resource_type, match.group(id_group))
        return None
    
    def check_access(self, resource_tenant_id: str, resource_owner_id: str, 
                     user_tenant_id: str, user_id: str, user_roles: list = None) -> tuple[bool, str]:
        """
        Cek akses dengan data resource REAL dari database.
        BUKAN dari JWT.
        """
        # Admin override
        if user_roles and "admin" in user_roles:
            logger.info(f"Admin override: {user_id}")
            return True, "Admin override"
        
        # Tenant isolation
        if resource_tenant_id != user_tenant_id:
            logger.warning(f"Tenant mismatch: resource={resource_tenant_id}, user={user_tenant_id}")
            return False, "Tenant mismatch"
        
        # Owner isolation
        if resource_owner_id and resource_owner_id != user_id:
            logger.warning(f"Owner mismatch: resource={resource_owner_id}, user={user_id}")
            return False, "Resource belongs to another user"
        
        return True, "Access granted"
    
    def validate_request(self, resource: Resource, user_tenant_id: str, user_id: str, user_roles: list = None) -> tuple[bool, str]:
        """
        Validate request dengan resource dari database.
        """
        return self.check_access(
            resource_tenant_id=resource.tenant_id,
            resource_owner_id=resource.owner_id,
            user_tenant_id=user_tenant_id,
            user_id=user_id,
            user_roles=user_roles
        )

class BOLAProtection:
    def __init__(self, auth_middleware: AuthorizationMiddleware):
        self.auth_middleware = auth_middleware
    
    def protect(self, resource_type: str, resource_id_param: str = "resource_id"):
        def decorator(func):
            from functools import wraps
            
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Ambil resource_id dari parameter
                resource_id = kwargs.get(resource_id_param)
                user_tenant_id = kwargs.get("current_user", {}).get("tenant_id")
                user_id = kwargs.get("current_user", {}).get("sub")
                user_roles = kwargs.get("current_user", {}).get("roles", [])
                
                if not resource_id:
                    raise ValueError(f"Resource ID param '{resource_id_param}' not found")
                
                if not user_tenant_id:
                    raise ValueError("User tenant_id not found")
                
                # Fetch resource dari database (harus dipanggil di endpoint)
                # Endpoint harus fetch dulu, terus panggil check_access
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator

def get_authorization_middleware() -> AuthorizationMiddleware:
    return AuthorizationMiddleware()
