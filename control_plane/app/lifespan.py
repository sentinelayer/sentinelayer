from contextlib import asynccontextmanager
from fastapi import FastAPI
from control_plane.app.infrastructure.db.session import engine
from control_plane.app.infrastructure.db.models import Base
from control_plane.app.infrastructure.security.provenance import provenance

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    provenance.verify()
    yield
    # Shutdown
    engine.dispose()
