from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from control_plane.app.api.v1.router import router
from control_plane.app.lifespan import lifespan
from control_plane.app.middleware.auth import AuthMiddleware
from control_plane.app.middleware.tenant import TenantMiddleware
from control_plane.app.infrastructure.db.rls import enable_rls
import os

app = FastAPI(title="SentinelLayer Control Plane", version="0.1.0", lifespan=lifespan)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuthMiddleware)
app.add_middleware(TenantMiddleware)

enable_rls()

app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"status": "ok", "service": "SentinelLayer Control Plane"}
