from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from typing import Any

import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from engine.behavior import behavior_engine

app = FastAPI(title="SentinelLayer Behavior Engine", version="1.0.0")


class BehaviorRequest(BaseModel):
    tenant_id: str = Field(default="", max_length=128)
    application_id: str = Field(default="default", max_length=128)
    environment: str = Field(default="production", max_length=32)
    endpoint: str = Field(min_length=1, max_length=2048)
    user_id: str = Field(default="", max_length=256)
    session_id: str = Field(default="", max_length=256)
    client_id: str = Field(default="", max_length=256)
    resource_type: str = Field(default="", max_length=128)
    resource_id: str = Field(default="", max_length=256)
    business_operation: str = Field(default="", max_length=128)
    sensitivity: str = Field(default="internal", max_length=32)
    criticality: str = Field(default="normal", max_length=32)


class SharedBehaviorState:
    def __init__(self) -> None:
        self.redis_client: redis.Redis | None = None
        configured_url = os.getenv("REDIS_URL", "").strip()
        production = os.getenv("SL_ENV", "development").lower() in {"production", "prod"}
        if configured_url:
            self.redis_client = redis.Redis.from_url(configured_url, decode_responses=True)
        elif production:
            raise RuntimeError("REDIS_URL is required for shared behavior state in production")

    @staticmethod
    def _scoped_actor(req: BehaviorRequest) -> str:
        actor = req.user_id or req.session_id or req.client_id or "anonymous"
        scope = req.tenant_id or "public"
        digest = hashlib.sha256(f"{scope}\x00{actor}".encode("utf-8")).hexdigest()
        return f"actor:{digest}"

    @staticmethod
    def _sequence_anomaly(actions: list[str]) -> dict[str, Any]:
        patterns = [
            ["login", "add_payment", "coupon", "refund"],
            ["login", "password_reset", "password_reset", "password_reset"],
        ]
        for pattern in patterns:
            position = 0
            for action in actions:
                if action == pattern[position] or action.endswith(pattern[position]) or pattern[position] in action:
                    position += 1
                    if position == len(pattern):
                        return {"is_anomaly": True, "reason": "business_flow_abuse", "confidence": 0.75, "signals": ["sequence_fraud"], "pattern": pattern}
        return {"is_anomaly": False, "reason": "no_fraud_pattern", "confidence": 0.3, "signals": []}

    def analyze(self, req: BehaviorRequest) -> dict[str, Any]:
        actor = self._scoped_actor(req)
        if self.redis_client is None:
            context = req.model_dump()
            context["user_id"] = actor
            return behavior_engine.analyze(context)
        now = time.time()
        key = f"sl:behavior:actions:{actor}"
        member = json.dumps({"endpoint": req.endpoint, "timestamp": now, "nonce": uuid.uuid4().hex}, sort_keys=True)
        try:
            pipe = self.redis_client.pipeline(transaction=True)
            pipe.zremrangebyscore(key, 0, now - 300)
            pipe.zadd(key, {member: now})
            pipe.expire(key, 305)
            pipe.zrange(key, 0, -1)
            entries = pipe.execute()[3]
        except redis.RedisError as exc:
            raise HTTPException(status_code=503, detail="shared behavior state unavailable") from exc

        actions: list[str] = []
        for raw in entries[-50:]:
            try:
                value = json.loads(raw)
                if isinstance(value, dict) and isinstance(value.get("endpoint"), str):
                    actions.append(value["endpoint"])
            except (TypeError, json.JSONDecodeError):
                continue
        frequency = {"is_anomaly": False, "reason": "normal", "confidence": 0.4, "signals": [], "count": len(entries)}
        if len(entries) > 50:
            frequency = {"is_anomaly": True, "reason": "excessive_requests_5m", "confidence": 0.85, "signals": ["freq_critical"], "count": len(entries)}
        elif len(entries) > 20:
            frequency = {"is_anomaly": True, "reason": "elevated_request_rate_5m", "confidence": 0.65, "signals": ["freq_elevated"], "count": len(entries)}
        sequence = self._sequence_anomaly(actions)
        signals = list(dict.fromkeys([*(frequency["signals"]), *(sequence["signals"])]))
        return {
            "is_anomaly": bool(frequency["is_anomaly"] or sequence["is_anomaly"]),
            "confidence": max(float(frequency["confidence"]), float(sequence["confidence"])),
            "signals": signals,
            "frequency": frequency,
            "sequence": sequence,
        }


state = SharedBehaviorState()


def _scoped_actor(req: BehaviorRequest) -> str:
    return state._scoped_actor(req)


@app.get("/health")
def health() -> dict[str, Any]:
    if state.redis_client is not None:
        try:
            state.redis_client.ping()
        except redis.RedisError as exc:
            raise HTTPException(status_code=503, detail={"status": "not_ready", "behavior_store": "unavailable"}) from exc
    return {"status": "healthy", "service": "behavior-engine", "version": "1.0.0", "state_store": "redis" if state.redis_client else "memory-dev-only"}


@app.post("/v1/analyze")
def analyze(req: BehaviorRequest) -> dict[str, Any]:
    if not req.tenant_id and not req.client_id and not req.user_id and not req.session_id:
        raise HTTPException(status_code=400, detail="behavior scope is required")
    result = state.analyze(req)
    result["engine_version"] = "1.0.0"
    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "engine.behavior.server:app",
        host="127.0.0.1",
        port=int(os.getenv("BEHAVIOR_ENGINE_PORT", "8091")),
        reload=False,
    )
