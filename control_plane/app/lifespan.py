import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from control_plane.app.runtime import is_production

from control_plane.app.infrastructure.db.models import Base
from control_plane.app.infrastructure.db.session import auth_engine, engine, worker_engine
from control_plane.app.infrastructure.security.provenance import provenance
from control_plane.app.infrastructure.db.privileges import validate_database_roles


@asynccontextmanager
async def lifespan(app: FastAPI):
    production = is_production()
    auto_create = os.getenv("SL_AUTO_CREATE_SCHEMA", "0" if production else "1")
    if production and os.getenv("MIGRATION_DATABASE_URL", "").strip():
        raise RuntimeError("Migration credentials must not be exposed to the production runtime")
    if production and auto_create != "0":
        raise RuntimeError("SL_AUTO_CREATE_SCHEMA must be 0 in production")
    enforce_runtime_digest = os.getenv("SL_ENFORCE_PROVENANCE", "0").strip().lower() in {"1", "true"}
    enforce_manifest = production or enforce_runtime_digest
    if enforce_manifest:
        manifest_result = provenance.verify()
        if not manifest_result.get("verified"):
            raise RuntimeError(f"Runtime provenance manifest verification failed: {manifest_result.get('reason')}")
    if enforce_runtime_digest:
        approved_hash = os.getenv("SL_APPROVED_ARTIFACT_HASH", "")
        runtime_result = provenance.verify_container("control-plane", approved_hash)
        if not runtime_result.get("verified"):
            raise RuntimeError("Running artifact does not match the approved artifact digest")
    if production:
        validate_database_roles(engine, auth_engine, worker_engine)
    if auto_create == "1":
        Base.metadata.create_all(bind=engine)
    try:
        yield
    finally:
        engine.dispose()
        if auth_engine is not engine:
            auth_engine.dispose()
        if worker_engine is not engine and worker_engine is not auth_engine:
            worker_engine.dispose()
