from fastapi import APIRouter
from control_plane.app.api.v1 import auth, metrics, health

router = APIRouter()

router.include_router(auth.router)
router.include_router(metrics.router)
router.include_router(health.router)
