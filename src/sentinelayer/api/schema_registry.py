from fastapi import APIRouter
from src.sentinelayer.api.schema import router as schema_router

def register_schemas(app):
    app.include_router(schema_router, prefix="/api/v1/schema", tags=["schema"])
