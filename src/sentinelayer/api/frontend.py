from fastapi import APIRouter
from fastapi.responses import HTMLResponse
import os

router = APIRouter(tags=["frontend"])

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    path = "frontend/build/index.html"
    if os.path.exists(path):
        with open(path, "r") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h1>Dashboard not built. Run npm build first.</h1>")
