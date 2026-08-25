from typing import List, Optional

class Permission:
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    MANAGE_TENANTS = "manage_tenants"
    MANAGE_USERS = "manage_users"
    MANAGE_POLICIES = "manage_policies"
    VIEW_EVIDENCE = "view_evidence"
    MANAGE_KEYS = "manage_keys"
    TOGGLE_KILLSWITCH = "toggle_killswitch"

ROLE_PERMISSIONS = {
    "user": [Permission.READ, Permission.WRITE],
    "admin": [
        Permission.READ, Permission.WRITE, Permission.DELETE,
        Permission.MANAGE_TENANTS, Permission.MANAGE_USERS,
        Permission.MANAGE_POLICIES, Permission.VIEW_EVIDENCE,
        Permission.MANAGE_KEYS, Permission.TOGGLE_KILLSWITCH
    ],
    "viewer": [Permission.READ],
    "auditor": [Permission.READ, Permission.VIEW_EVIDENCE],
}

def has_permission(user_roles: List[str], required_permission: str) -> bool:
    if not user_roles:
        return False
    for role in user_roles:
        if role in ROLE_PERMISSIONS:
            if required_permission in ROLE_PERMISSIONS[role]:
                return True
    return False

def require_permission(required_permission: str):
    from fastapi import HTTPException, status
    def decorator(func):
        from functools import wraps
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(status_code=401, detail="Not authenticated")
            roles = current_user.get("roles", [])
            if not has_permission(roles, required_permission):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            return await func(*args, **kwargs)
        return wrapper
    return decorator
