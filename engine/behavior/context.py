"""Application Context Contract — Section 11.22."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ApplicationContext(BaseModel):
    tenant_id: str = ""
    application_id: str = "default"
    environment: str = "production"
    endpoint: str = ""
    user_id: str = ""
    session_id: str = ""
    resource_type: str = ""
    resource_id: str = ""
    business_operation: str = ""
    sensitivity: str = "internal"
    criticality: str = "normal"

    def to_behavior_dict(self) -> dict[str, Any]:
        return self.model_dump()


def from_headers(headers: dict[str, str], path: str = "") -> ApplicationContext:
    return ApplicationContext(
        tenant_id=headers.get("x-tenant-id") or headers.get("X-Tenant-ID") or "",
        application_id=headers.get("x-application-id") or headers.get("X-Application-ID") or "default",
        environment=headers.get("x-environment") or "production",
        endpoint=path,
        user_id=headers.get("x-user-id") or headers.get("X-User-ID") or "",
        session_id=headers.get("x-session-id") or headers.get("X-Session-ID") or "",
        resource_type=headers.get("x-resource-type") or "",
        resource_id=headers.get("x-resource-id") or "",
        business_operation=headers.get("x-business-op") or "",
        sensitivity=headers.get("x-sensitivity") or "internal",
        criticality=headers.get("x-criticality") or "normal",
    )
