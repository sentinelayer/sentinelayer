from fastapi import APIRouter
from control_plane.app.api.v1 import (
    auth,
    tenants,
    applications,
    policies,
    health,
)

router = APIRouter()
router.include_router(auth.router)
router.include_router(tenants.router)
router.include_router(applications.router)
router.include_router(policies.router)
router.include_router(health.router)
