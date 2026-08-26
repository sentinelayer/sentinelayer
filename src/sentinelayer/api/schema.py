from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
import json
import hashlib

router = APIRouter(prefix="/api/v1/schema", tags=["schema"])

class SchemaResponse(BaseModel):
    schema_id: str
    version: str
    schema: Dict[str, Any]

SCHEMA_REGISTRY = {}

@router.post("/register")
async def register_schema(schema_id: str, version: str, schema: Dict[str, Any]) -> Dict:
    schema_hash = hashlib.sha256(json.dumps(schema, sort_keys=True).encode()).hexdigest()
    
    SCHEMA_REGISTRY[f"{schema_id}:{version}"] = {
        "schema_id": schema_id,
        "version": version,
        "schema": schema,
        "hash": schema_hash
    }
    
    return {"registered": True, "schema_id": schema_id, "version": version, "hash": schema_hash}

@router.get("/{schema_id}/{version}")
async def get_schema(schema_id: str, version: str) -> SchemaResponse:
    key = f"{schema_id}:{version}"
    if key not in SCHEMA_REGISTRY:
        return {"error": "Schema not found"}
    
    data = SCHEMA_REGISTRY[key]
    return SchemaResponse(
        schema_id=data["schema_id"],
        version=data["version"],
        schema=data["schema"]
    )

@router.get("/{schema_id}")
async def list_versions(schema_id: str) -> Dict:
    versions = [
        k.split(":")[1] for k in SCHEMA_REGISTRY.keys()
        if k.startswith(f"{schema_id}:")
    ]
    return {"schema_id": schema_id, "versions": sorted(versions)}
