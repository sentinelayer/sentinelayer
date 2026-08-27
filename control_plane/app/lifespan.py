import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from control_plane.app.infrastructure.db.models import Base
from control_plane.app.infrastructure.db.session import engine
from control_plane.app.infrastructure.security.provenance import provenance


@asynccontextmanager
async def lifespan(app: FastAPI):
    environment = os.getenv("SL_ENV", "development").lower()
    auto_create = os.getenv("SL_AUTO_CREATE_SCHEMA", "0" if environment == "production" else "1")
    if auto_create == "1":
        Base.metadata.create_all(bind=engine)
    enforce_manifest = environment in {"production", "prod"} or os.getenv("SL_ENFORCE_PROVENANCE", "false").lower() == "true"
    enforce_runtime_digest = os.getenv("SL_ENFORCE_PROVENANCE", "false").lower() == "true"
    if enforce_manifest:
        manifest_result = provenance.verify()
        if not manifest_result.get("verified"):
            raise RuntimeError(f"Runtime provenance manifest verification failed: {manifest_result.get('reason')}")
    if enforce_runtime_digest:
        approved_hash = os.getenv("SL_APPROVED_ARTIFACT_HASH", "")
        runtime_result = provenance.verify_container("control-plane", approved_hash)
        if not runtime_result.get("verified"):
            raise RuntimeError("Running artifact does not match the approved artifact digest")
    yield
    engine.dispose()
