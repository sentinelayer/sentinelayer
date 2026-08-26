from fastapi import APIRouter
from control_plane.app.api.v1 import (
    auth, tenants, applications, users, policies,
    incidents, evidence, metrics, health
)

router = APIRouter()

router.include_router(auth.router)
router.include_router(tenants.router)
router.include_router(applications.router)
router.include_router(users.router)
router.include_router(policies.router)
router.include_router(incidents.router)
router.include_router(evidence.router)
router.include_router(metrics.router)
router.include_router(health.router)
