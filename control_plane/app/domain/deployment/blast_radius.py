from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class DeployMode(str, Enum):
    SINGLE_TENANT = "single-tenant"
    PERCENTAGE = "percentage"


class Stage(str, Enum):
    INTERNAL = "internal"
    DESIGN_PARTNER = "design_partner"
    PILOT_2 = "pilot_2"
    PILOT_3 = "pilot_3"
    ALL_PILOT = "all_pilot"
    PCT_5 = "5%"
    PCT_25 = "25%"
    PCT_50 = "50%"
    PCT_100 = "100%"


@dataclass
class RollbackTrigger:
    name: str
    threshold: float
    current: float = 0.0

    def tripped(self) -> bool:
        return self.current >= self.threshold


@dataclass
class BlastRadius:
    mode: DeployMode = DeployMode.SINGLE_TENANT
    stage: Stage = Stage.INTERNAL
    canary_percentage: int = 5
    tenants: list[str] = field(default_factory=list)
    deployment_id: str = ""
    version: str = ""
    started_at: str = ""
    triggers: list[RollbackTrigger] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.triggers:
            self.triggers = [
                RollbackTrigger("fp_spike_pct", 10.0),
                RollbackTrigger("latency_ms", 50.0),
                RollbackTrigger("error_rate_pct", 5.0),
                RollbackTrigger("decision_divergence_pct", 5.0),
                RollbackTrigger("customer_complaint", 1.0),
            ]

    def add_tenant(self, tenant_id: str) -> None:
        if tenant_id not in self.tenants:
            self.tenants.append(tenant_id)

    def start(self, deployment_id: str, version: str, mode: DeployMode | None = None) -> dict[str, Any]:
        if mode:
            self.mode = mode
        self.deployment_id = deployment_id
        self.version = version
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.stage = Stage.INTERNAL if self.mode == DeployMode.SINGLE_TENANT else Stage.PCT_5
        return self.status()

    def advance(self) -> dict[str, Any]:
        if any(t.tripped() for t in self.triggers):
            return self.rollback(reason="auto_trigger")
        order_st = [Stage.INTERNAL, Stage.DESIGN_PARTNER, Stage.PILOT_2, Stage.PILOT_3, Stage.ALL_PILOT]
        order_pct = [Stage.PCT_5, Stage.PCT_25, Stage.PCT_50, Stage.PCT_100]
        order = order_st if self.mode == DeployMode.SINGLE_TENANT else order_pct
        try:
            idx = order.index(self.stage)
            if idx + 1 < len(order):
                self.stage = order[idx + 1]
                if self.mode == DeployMode.PERCENTAGE:
                    self.canary_percentage = int(self.stage.value.replace("%", "") or 5)
        except ValueError:
            pass
        return self.status()

    def record_metric(self, name: str, value: float) -> None:
        for t in self.triggers:
            if t.name == name:
                t.current = value

    def rollback(self, reason: str = "manual") -> dict[str, Any]:
        prev = self.stage
        self.stage = Stage.INTERNAL
        self.canary_percentage = 0
        return {
            "status": "rolled_back",
            "from_stage": prev.value,
            "reason": reason,
            "deployment_id": self.deployment_id,
            "version": self.version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "stage": self.stage.value,
            "canary_percentage": self.canary_percentage,
            "tenants": list(self.tenants),
            "deployment_id": self.deployment_id,
            "version": self.version,
            "started_at": self.started_at,
            "triggers": [
                {"name": t.name, "threshold": t.threshold, "current": t.current, "tripped": t.tripped()}
                for t in self.triggers
            ],
        }
