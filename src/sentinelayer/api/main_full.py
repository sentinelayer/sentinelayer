from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.sentinelayer.api import auth, health, metrics
import os

app = FastAPI(title="SentinelLayer API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(health.router)
app.include_router(metrics.router)

@app.get("/")
async def root():
    return {
        "service": "SentinelLayer",
        "version": "0.1.0",
        "status": "operational",
        "docs": "/docs",
        "auth": "/api/v1/auth",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/metrics")
async def metrics_endpoint():
    return {"status": "metrics endpoint"}
