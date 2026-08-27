import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from control_plane.app.infrastructure.db.models import Base
from control_plane.app.infrastructure.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    environment = os.getenv("SL_ENV", "development").lower()
    auto_create = os.getenv("SL_AUTO_CREATE_SCHEMA", "0" if environment == "production" else "1")
    if auto_create == "1":
        Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
