from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse
import os

router = APIRouter(tags=["frontend"])

@router.get("/app", response_class=HTMLResponse)
async def serve_app():
    index_path = "frontend/build/index.html"
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h1>Frontend not built. Run npm build first.</h1>")

@router.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    return await serve_app()
