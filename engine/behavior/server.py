from __future__ import annotations

import hashlib
import os
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from engine.behavior import behavior_engine

app = FastAPI(title="SentinelLayer Behavior Engine", version="1.0.0")


class BehaviorRequest(BaseModel):
    tenant_id: str = Field(default="", max_length=128)
    application_id: str = Field(default="default", max_length=128)
    environment: str = Field(default="production", max_length=32)
    endpoint: str = Field(min_length=1, max_length=2048)
    user_id: str = Field(default="", max_length=256)
    session_id: str = Field(default="", max_length=256)
    client_id: str = Field(default="", max_length=256)
    resource_type: str = Field(default="", max_length=128)
    resource_id: str = Field(default="", max_length=256)
    business_operation: str = Field(default="", max_length=128)
    sensitivity: str = Field(default="internal", max_length=32)
    criticality: str = Field(default="normal", max_length=32)


def _scoped_actor(req: BehaviorRequest) -> str:
    actor = req.user_id or req.session_id or req.client_id or "anonymous"
    scope = req.tenant_id or "public"
    digest = hashlib.sha256(f"{scope}\x00{actor}".encode("utf-8")).hexdigest()
    return f"actor:{digest}"


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "healthy", "service": "behavior-engine", "version": "1.0.0"}


@app.post("/v1/analyze")
def analyze(req: BehaviorRequest) -> dict[str, Any]:
    if not req.tenant_id and not req.client_id and not req.user_id and not req.session_id:
        raise HTTPException(status_code=400, detail="behavior scope is required")
    context = req.model_dump()
    context["user_id"] = _scoped_actor(req)
    result = behavior_engine.analyze(context)
    result["engine_version"] = "1.0.0"
    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "engine.behavior.server:app",
        host="127.0.0.1",
        port=int(os.getenv("BEHAVIOR_ENGINE_PORT", "8091")),
        reload=False,
    )
