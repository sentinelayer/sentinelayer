import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/schemas", tags=["schemas"])


class SchemaRegister(BaseModel):
    schema_id: str
    version: str
    schema_body: dict[str, Any] = Field(default_factory=dict, alias="schema")

    model_config = {"populate_by_name": True}


SCHEMAS: dict[str, Any] = {}


@router.post("/register")
async def register_schema(data: SchemaRegister):
    body = data.schema_body
    key = f"{data.schema_id}:{data.version}"
    hash_val = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    SCHEMAS[key] = {
        "schema_id": data.schema_id,
        "version": data.version,
        "schema": body,
        "hash": hash_val,
        "registered_at": datetime.now(UTC).isoformat(),
    }
    return {"status": "registered", "key": key, "hash": hash_val}


@router.get("/{schema_id}/{version}")
async def get_schema(schema_id: str, version: str):
    key = f"{schema_id}:{version}"
    if key not in SCHEMAS:
        return {"error": "Schema not found"}
    return SCHEMAS[key]


@router.get("/{schema_id}")
async def list_versions(schema_id: str):
    versions = [k.split(":")[1] for k in SCHEMAS if k.startswith(f"{schema_id}:")]
    return {"schema_id": schema_id, "versions": versions}
