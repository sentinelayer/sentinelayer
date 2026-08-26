from fastapi import FastAPI
from src.sentinelayer.api import auth, health
from src.sentinelayer.api.routes import orders
from src.sentinelayer.database import engine
from src.sentinelayer.database.models import Base
import os

app = FastAPI(title="SentinelLayer API", version="0.1.0")

# Create tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(auth.router)
app.include_router(health.router)
app.include_router(orders.router)

@app.get("/")
async def root():
    return {
        "service": "SentinelLayer",
        "version": "0.1.0",
        "status": "operational",
        "docs": "/docs",
        "auth": "/api/v1/auth",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "testing": False
    }

@app.get("/metrics")
async def metrics():
    return {"status": "metrics endpoint"}
