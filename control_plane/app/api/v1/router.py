from fastapi import APIRouter

from control_plane.app.api.v1 import (
    ai_assist,
    alerts,
    applications,
    attack_graph,
    audit,
    auth,
    configuration,
    behavior,
    compliance,
    events,
    events_ws,
    evidence,
    explainability,
    gates,
    health,
    heatmap,
    high_risk_actions,
    incidents,
    metrics,
    offboarding,
    policies,
    residency,
    risk_calibration,
    schema,
    sla,
    tenants,
    threat_intel,
    user_risk,
    users,
    webhooks,
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
router.include_router(compliance.router)
router.include_router(explainability.router)
router.include_router(high_risk_actions.router)
router.include_router(breakglass.router)
router.include_router(behavior.router)
router.include_router(residency.router)
router.include_router(risk_calibration.router)
router.include_router(events.router)
router.include_router(events_ws.router)
router.include_router(offboarding.router)
router.include_router(threat_intel.router)
router.include_router(ai_assist.router)
