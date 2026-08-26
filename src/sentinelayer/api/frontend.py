from fastapi import APIRouter
from fastapi.responses import HTMLResponse
import os

router = APIRouter(tags=["frontend"])

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    html_path = "frontend/index.html"
    if os.path.exists(html_path):
        with open(html_path, "r") as f:
            return f.read()
    return "<h1>Dashboard not found</h1>"

@router.get("/app", response_class=HTMLResponse)
async def app_page():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>SentinelLayer</title></head>
    <body>
        <h1>SentinelLayer API</h1>
        <p>Visit <a href="/docs">/docs</a> for API documentation</p>
        <p>Visit <a href="/dashboard">/dashboard</a> for security dashboard</p>
    </body>
    </html>
    """
