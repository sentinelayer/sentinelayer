from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/attack-graph", tags=["attack-graph"])

ATTACK_DATA = {
    "nodes": [
        {"id": "external", "name": "External", "type": "source"},
        {"id": "waf", "name": "WAF", "type": "control"},
        {"id": "auth", "name": "Auth", "type": "control"},
        {"id": "api", "name": "API", "type": "target"},
        {"id": "db", "name": "Database", "type": "target"}
    ],
    "edges": [
        {"source": "external", "target": "waf"},
        {"source": "external", "target": "auth"},
        {"source": "waf", "target": "api"},
        {"source": "auth", "target": "api"},
        {"source": "api", "target": "db"}
    ]
}

@router.get("/")
async def get_attack_graph():
    return {
        **ATTACK_DATA,
        "generated_at": datetime.utcnow().isoformat()
    }

@router.get("/paths")
async def get_attack_paths():
    return {
        "paths": [
            ["external", "waf", "api", "db"],
            ["external", "auth", "api", "db"]
        ]
    }
