from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from control_plane.app.api.v1 import auth, metrics, health

app = FastAPI(title="SentinelLayer Control Plane", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(metrics.router)
app.include_router(health.router)

@app.get("/")
async def root():
    return {"status": "ok", "service": "SentinelLayer Control Plane"}
