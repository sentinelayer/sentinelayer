from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any
import os

router = APIRouter(prefix="/configuration", tags=["configuration"])

CONFIG: dict[str, Any] = {
    "environment": os.getenv("ENVIRONMENT", "development"),
    "rate_limit": int(os.getenv("RATE_LIMIT", "60")),
    "jwt_expiry_minutes": 15,
    "mfa_enabled": True,
    "waf_enabled": True,
    "threat_intel_enabled": True,
    "log_level": os.getenv("LOG_LEVEL", "info"),
    "version": "0.1.0",
}


class ConfigUpdate(BaseModel):
    key: str
    value: Any


@router.get("/")
@router.get("")
async def get_configuration():
    return CONFIG


@router.put("/")
@router.put("")
async def update_configuration(data: ConfigUpdate):
    if data.key in CONFIG:
        CONFIG[data.key] = data.value
        return {"key": data.key, "value": data.value, "updated": True}
    return {"error": "Config key not found"}
