from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/residency", tags=["residency"])

class ResidencyRule(BaseModel):
    data_type: str
    primary_region: str
    backup_region: str

RULES = []

@router.post("/rules")
async def create_rule(rule: ResidencyRule):
    RULES.append(rule.dict())
    return rule

@router.get("/rules")
async def list_rules():
    return RULES

@router.get("/enforce/{data_type}/{region}")
async def enforce_residency(data_type: str, region: str):
    for rule in RULES:
        if rule["data_type"] == data_type:
            if region == rule["primary_region"]:
                return {"allowed": True, "region": region}
            return {"allowed": False, "required_region": rule["primary_region"]}
    return {"allowed": True, "region": region}
