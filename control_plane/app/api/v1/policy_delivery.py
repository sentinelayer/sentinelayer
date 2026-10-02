"""Authenticated gateway reports, separate from privileged policy mutations."""
import base64
import binascii
import json
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy.orm import Session

from control_plane.app.api.deps import db_with_tenant, tenant_id
from control_plane.app.api.v1.policies import GatewayRuntimeRules, _signer, _signature_valid, _rules
from control_plane.app.domain.events import append_event
from control_plane.app.infrastructure.db.models import GatewayPolicyDelivery, PolicyVersion

router = APIRouter(prefix="/gateway-policy", tags=["policy-delivery"])


class SignedBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")
    payload: str = Field(max_length=131072)
    signature: str = Field(max_length=256)
    key_id: str = Field(max_length=128)


class DeliveryReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid")
    gateway_id: str = Field(pattern=r"^[A-Za-z0-9_.-]{1,64}$")
    bundle: SignedBundle


class RuntimePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    policy_id: str
    tenant_id: str
    application_id: str | None
    version: int = Field(ge=1, strict=True)
    issued_at: int = Field(strict=True)
    expires_at: int = Field(strict=True)
    rules: GatewayRuntimeRules


@router.post("/ack")
async def acknowledge_policy(body: DeliveryReceipt, request: Request, db: Session = Depends(db_with_tenant)):
    tid = tenant_id(request)
    if getattr(request.state, "auth_method", None) != "api_key":
        raise HTTPException(status_code=403, detail="Gateway receipt requires its registered service API key")
    row = db.query(GatewayPolicyDelivery).filter(
        GatewayPolicyDelivery.tenant_id == tid, GatewayPolicyDelivery.gateway_id == body.gateway_id,
        GatewayPolicyDelivery.service_user_id == getattr(request.state, "user_id", None),
    ).with_for_update().first()
    if not row:
        raise HTTPException(status_code=404, detail="Gateway binding not found")
    try:
        raw = base64.b64decode(body.bundle.payload, validate=True)
        if len(raw) > 65536:
            raise ValueError("Bundle too large")
        decoded = json.loads(raw)
        if raw != _signer.canonical(decoded) or not _signer.verify(decoded, body.bundle.signature, body.bundle.key_id):
            raise ValueError("Invalid signature")
        payload = RuntimePayload.model_validate(decoded)
    except (ValueError, TypeError, binascii.Error, ValidationError) as exc:
        raise HTTPException(status_code=409, detail="Invalid signed policy receipt") from exc
    now = int(datetime.now(UTC).timestamp())
    if (payload.tenant_id != tid or payload.policy_id != row.policy_id
            or payload.expires_at <= now or payload.issued_at > now + 30
            or not 0 < payload.expires_at - payload.issued_at <= 60):
        raise HTTPException(status_code=409, detail="Receipt identity or validity window rejected")
    version = db.query(PolicyVersion).filter_by(tenant_id=tid, policy_id=row.policy_id, version=payload.version).first()
    if not version or not _signature_valid(version):
        raise HTTPException(status_code=409, detail="Receipt policy version is not trusted")
    try:
        expected_rules = GatewayRuntimeRules.model_validate(_rules(version.rules).get("gateway"))
    except ValidationError as exc:
        raise HTTPException(status_code=409, detail="Stored gateway policy is invalid") from exc
    if payload.rules != expected_rules:
        raise HTTPException(status_code=409, detail="Receipt rules do not match the stored version")
    if row.reported_version is not None and (payload.version < row.reported_version or
            (payload.version == row.reported_version and payload.issued_at < row.issued_at)):
        raise HTTPException(status_code=409, detail="Receipt rollback rejected")
    changed = payload.version != row.reported_version
    row.reported_version = payload.version
    row.issued_at, row.expires_at = payload.issued_at, payload.expires_at
    row.signing_key_id = body.bundle.key_id
    row.reported_at = datetime.now(UTC)
    if changed:
        append_event(db, tid, "policy.gateway_reported", data={"gateway_id": row.gateway_id,
                     "policy_id": row.policy_id, "version": payload.version})
    db.commit()
    return {"gateway_id": row.gateway_id, "reported_version": row.reported_version}
