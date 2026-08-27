from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from control_plane.app.api.deps import db_with_tenant, tenant_id
from control_plane.app.infrastructure.db.models import SchemaRecord

router = APIRouter(prefix="/schemas", tags=["schemas"])


class SchemaRegister(BaseModel):
    schema_id: str = Field(min_length=1, max_length=128)
    version: str = Field(min_length=1, max_length=64)
    schema_body: dict[str, Any] = Field(default_factory=dict, alias="schema")
    model_config = {"populate_by_name": True}


@router.post("/register")
async def register_schema(data: SchemaRegister, request: Request, db: Session = Depends(db_with_tenant)):
    tid = tenant_id(request)
    existing = db.query(SchemaRecord).filter(
        SchemaRecord.tenant_id == tid, SchemaRecord.schema_id == data.schema_id, SchemaRecord.version == data.version
    ).first()
    hash_val = hashlib.sha256(json.dumps(data.schema_body, sort_keys=True).encode()).hexdigest()
    if existing:
        if existing.hash_value != hash_val:
            raise HTTPException(status_code=409, detail="Schema version already exists with different content")
        return {"status": "unchanged", "key": f"{data.schema_id}:{data.version}", "hash": hash_val}
    record = SchemaRecord(
        id=str(uuid.uuid4()), tenant_id=tid, schema_id=data.schema_id, version=data.version,
        schema_body=json.dumps(data.schema_body, sort_keys=True), hash_value=hash_val, registered_at=datetime.now(UTC),
    )
    db.add(record)
    db.commit()
    return {"status": "registered", "key": f"{data.schema_id}:{data.version}", "hash": hash_val}


@router.get("/{schema_id}/{version}")
async def get_schema(schema_id: str, version: str, request: Request, db: Session = Depends(db_with_tenant)):
    record = db.query(SchemaRecord).filter(
        SchemaRecord.tenant_id == tenant_id(request), SchemaRecord.schema_id == schema_id, SchemaRecord.version == version
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Schema not found")
    return {"schema_id": record.schema_id, "version": record.version, "schema": json.loads(record.schema_body),
            "hash": record.hash_value, "registered_at": record.registered_at.isoformat()}


@router.get("/{schema_id}")
async def list_versions(schema_id: str, request: Request, db: Session = Depends(db_with_tenant)):
    records = db.query(SchemaRecord).filter(
        SchemaRecord.tenant_id == tenant_id(request), SchemaRecord.schema_id == schema_id
    ).order_by(SchemaRecord.registered_at.desc()).all()
    return {"schema_id": schema_id, "versions": [record.version for record in records]}
