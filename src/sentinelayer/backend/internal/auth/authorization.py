from typing import Optional, Dict, Any
from dataclasses import dataclass
import re

@dataclass
class Resource:
    """Resource representation untuk authorization check"""
    type: str  # 'order', 'user', 'payment', 'product'
    id: str
    tenant_id: str
    owner_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AuthorizationMiddleware:
    """
    BOLA/IDOR Protection (Section 8.19)
    Memastikan user hanya bisa akses resource miliknya sendiri
    """
    
    def __init__(self):
        # Mapping endpoint -> resource extraction
        self.resource_patterns = {
            r"^/api/v1/orders/([^/]+)$": ("order", 1),
            r"^/api/v1/users/([^/]+)$": ("user", 1),
            r"^/api/v1/payments/([^/]+)$": ("payment", 1),
            r"^/api/v1/products/([^/]+)$": ("product", 1),
            r"^/api/v1/invoices/([^/]+)$": ("invoice", 1),
            r"^/api/v1/transactions/([^/]+)$": ("transaction", 1),
        }
    
    def extract_resource_from_path(self, path: str) -> Optional[tuple[str, str]]:
        """Extract resource type and ID from URL path"""
        for pattern, (resource_type, id_group) in self.resource_patterns.items():
            match = re.match(pattern, path)
            if match:
                resource_id = match.group(id_group)
                return (resource_type, resource_id)
        return None
    
    def check_access(
        self,
        resource: Resource,
        user_tenant_id: str,
        user_id: str,
        user_roles: list[str] = None
    ) -> tuple[bool, str]:
        """
        Check if user can access resource
        
        Returns:
            (allowed: bool, reason: str)
        """
        # 1. Admin/Superuser bisa akses semua (dengan audit)
        if user_roles and "admin" in user_roles:
            return True, "Admin override (audited)"
        
        # 2. Tenant isolation: MUST match
        if resource.tenant_id != user_tenant_id:
            return False, f"Tenant mismatch: {resource.tenant_id} vs {user_tenant_id}"
        
        # 3. Object ownership: user must own the resource
        if resource.owner_id and resource.owner_id != user_id:
            return False, f"Resource owner {resource.owner_id} != user {user_id}"
        
        return True, "Access granted"
    
    def validate_request(
        self,
        path: str,
        method: str,
        user_tenant_id: str,
        user_id: str,
        user_roles: list[str] = None,
        resource_id_from_body: Optional[str] = None
    ) -> tuple[bool, str]:
        """
        Validate request untuk BOLA/IDOR
        
        Args:
            path: URL path (e.g., /api/v1/orders/order-123)
            method: HTTP method (GET, POST, PUT, DELETE)
            user_tenant_id: Tenant ID dari JWT
            user_id: User ID dari JWT
            user_roles: List roles dari JWT
            resource_id_from_body: Optional resource ID dari request body
        """
        
        # Extract resource dari URL
        extracted = self.extract_resource_from_path(path)
        
        if extracted:
            resource_type, resource_id = extracted
            
            # Buat resource object
            resource = Resource(
                type=resource_type,
                id=resource_id,
                tenant_id=user_tenant_id,  # Assume same tenant from JWT
                owner_id=user_id  # Assume same owner from JWT
            )
            
            return self.check_access(resource, user_tenant_id, user_id, user_roles)
        
        # No resource ID in path (e.g., /api/v1/orders)
        # Check body for resource ID (POST/PUT requests)
        if resource_id_from_body and method in ["POST", "PUT"]:
            resource = Resource(
                type="unknown",
                id=resource_id_from_body,
                tenant_id=user_tenant_id,
                owner_id=user_id
            )
            return self.check_access(resource, user_tenant_id, user_id, user_roles)
        
        # Collection endpoints (no specific resource) -> allowed
        return True, "Collection access allowed"

class BOLAProtection:
    """
    BOLA Protection decorator untuk FastAPI endpoints
    """
    
    def __init__(self, auth_middleware: AuthorizationMiddleware):
        self.auth_middleware = auth_middleware
    
    def protect(
        self,
        resource_type: str,
        resource_id_param: str = "resource_id"
    ):
        """
        Decorator untuk protect endpoint dari BOLA
        
        Usage:
            @bola.protect(resource_type="order", resource_id_param="order_id")
            async def get_order(order_id: str, current_user: dict):
                ...
        """
        def decorator(func):
            from functools import wraps
            
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract resource_id from kwargs
                resource_id = kwargs.get(resource_id_param)
                user_tenant_id = kwargs.get("current_user", {}).get("tenant_id")
                user_id = kwargs.get("current_user", {}).get("user_id")
                user_roles = kwargs.get("current_user", {}).get("roles", [])
                
                if not resource_id:
                    raise ValueError(f"Resource ID param '{resource_id_param}' not found")
                
                if not user_tenant_id:
                    raise ValueError("User tenant_id not found")
                
                # Check access
                resource = Resource(
                    type=resource_type,
                    id=resource_id,
                    tenant_id=user_tenant_id,
                    owner_id=user_id
                )
                
                allowed, reason = self.auth_middleware.check_access(
                    resource, user_tenant_id, user_id, user_roles
                )
                
                if not allowed:
                    raise PermissionError(f"BOLA Protection: {reason}")
                
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator
