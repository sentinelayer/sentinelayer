from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="SentinelLayer API",
    description="Security control and enforcement platform",
    version="0.1.0"
)

# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "SentinelLayer",
        "version": "0.1.0",
        "status": "operational",
        "docs": "/docs"
    }

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

# Simple echo endpoint (test) - FIXED
@app.post("/echo")
async def echo(request: Request):
    body = await request.json()
    return {"echo": body, "timestamp": time.time()}

# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "path": request.url.path}
    )
