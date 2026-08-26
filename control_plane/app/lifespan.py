from contextlib import asynccontextmanager
from fastapi import FastAPI
from control_plane.app.infrastructure.db.session import engine
from control_plane.app.infrastructure.db.models import Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
