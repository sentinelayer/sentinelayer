from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from control_plane.app.api.v1.router import router
from control_plane.app.lifespan import lifespan

app = FastAPI(title="SentinelLayer Control Plane", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"status": "ok", "service": "SentinelLayer Control Plane"}
