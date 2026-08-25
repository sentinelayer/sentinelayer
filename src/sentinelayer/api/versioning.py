from fastapi import FastAPI, APIRouter, Request
from typing import Dict, Any

class VersionedRouter:
    def __init__(self, prefix: str = ""):
        self.routers: Dict[str, APIRouter] = {}
        self.current_version = "v1"
    
    def register(self, version: str, router: APIRouter):
        self.routers[version] = router
    
    def get_router(self, version: str = None) -> APIRouter:
        if version is None:
            version = self.current_version
        return self.routers.get(version)
    
    def mount(self, app: FastAPI, base_path: str = "/api"):
        for version, router in self.routers.items():
            app.include_router(router, prefix=f"{base_path}/{version}")
    
    def get_versions(self) -> list:
        return list(self.routers.keys())

_versioned_router = None

def get_versioned_router():
    global _versioned_router
    if _versioned_router is None:
        _versioned_router = VersionedRouter()
    return _versioned_router
