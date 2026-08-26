from fastapi import APIRouter
from control_plane.app.api.v1 import (
    offboarding,
    auth,
    tenants,
    applications,
    users,
    policies,
    incidents,
    evidence,
    metrics,
    health,
    sla,
    schema,
    webhooks,
    audit,
    alerts,
    attack_graph,
    heatmap,
    user_risk,
    configuration,
    explainability,
    high_risk_actions,
    residency,
    events,
    events_ws,
    gates,
)
from control_plane.app.api.v1.admin import breakglass

router = APIRouter()

router.include_router(auth.router)
router.include_router(tenants.router)
router.include_router(applications.router)
router.include_router(users.router)
router.include_router(policies.router)
router.include_router(incidents.router)
router.include_router(evidence.router)
router.include_router(gates.router)
router.include_router(metrics.router)
router.include_router(health.router)
router.include_router(sla.router)
router.include_router(schema.router)
router.include_router(webhooks.router)
router.include_router(audit.router)
router.include_router(alerts.router)
router.include_router(attack_graph.router)
router.include_router(heatmap.router)
router.include_router(user_risk.router)
router.include_router(configuration.router)
router.include_router(explainability.router)
router.include_router(high_risk_actions.router)
router.include_router(breakglass.router)
router.include_router(residency.router)
router.include_router(events.router)
router.include_router(events_ws.router)
router.include_router(offboarding.router)
