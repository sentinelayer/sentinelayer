import difflib
import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from control_plane.app.api.deps import db_with_tenant, tenant_id
from control_plane.app.infrastructure.db.models import AuditEvent, Application, Policy, PolicyVersion

router = APIRouter(prefix="/policies", tags=["policies"])


class PolicyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    rules: dict[str, Any] = Field(default_factory=dict)
    application_id: str | None = None


class PolicyVersionCreate(BaseModel):
    rules: dict[str, Any] = Field(default_factory=dict)
    name: str | None = Field(default=None, min_length=1, max_length=255)


class PolicyRollback(BaseModel):
    reason: str = Field(default="manual rollback", min_length=1, max_length=2000)


def _actor_id(request: Request) -> str | None:
    return getattr(request.state, "user_id", None)


def _rules(value: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail="Stored policy rules are invalid JSON") from exc
    if not isinstance(parsed, dict):
        raise HTTPException(status_code=500, detail="Stored policy rules must be an object")
    return parsed


def _policy_dict(policy: Policy, latest: PolicyVersion | None = None) -> dict[str, Any]:
    return {
        "id": policy.id,
        "name": policy.name,
        "tenant_id": policy.tenant_id,
        "application_id": policy.application_id,
        "version": policy.current_version or (latest.version if latest else 1),
        "rules": _rules(policy.rules),
        "created_at": policy.created_at.isoformat() if policy.created_at else None,
    }


def _record_audit(
    db: Session,
    tenant: str,
    actor: str | None,
    action: str,
    resource_type: str,
    resource_id: str | None,
    detail: dict[str, Any],
) -> None:
    previous = (
        db.query(AuditEvent)
        .filter(AuditEvent.tenant_id == tenant)
        .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
        .first()
    )
    now = datetime.now(UTC)
    detail_json = json.dumps(detail, sort_keys=True, separators=(",", ":"))
    event_id = str(uuid.uuid4())
    digest_input = "|".join(
        [previous.event_hash if previous else "", tenant, actor or "", action,
         resource_type, resource_id or "", detail_json, now.isoformat(), event_id]
    )
    db.add(
        AuditEvent(
            id=event_id,
            tenant_id=tenant,
            actor_id=actor,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            detail=detail_json,
            previous_hash=previous.event_hash if previous else None,
            event_hash=hashlib.sha256(digest_input.encode()).hexdigest(),
            created_at=now,
        )
    )


def _get_policy(policy_id: str, tenant: str, db: Session) -> Policy:
    policy = db.query(Policy).filter(Policy.id == policy_id, Policy.tenant_id == tenant).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


def _ensure_initial_version(policy: Policy, db: Session, actor: str | None) -> PolicyVersion:
    latest = (
        db.query(PolicyVersion)
        .filter(PolicyVersion.policy_id == policy.id, PolicyVersion.tenant_id == policy.tenant_id)
        .order_by(PolicyVersion.version.desc())
        .first()
    )
    if latest:
        if not policy.current_version:
            policy.current_version = latest.version
        return latest
    version = PolicyVersion(
        id=str(uuid.uuid4()),
        policy_id=policy.id,
        tenant_id=policy.tenant_id,
        version=policy.current_version or 1,
        rules=policy.rules,
        created_by=actor,
        created_at=policy.created_at or datetime.now(UTC),
    )
    policy.current_version = version.version
    db.add(version)
    db.flush()
    return version


@router.post("/")
@router.post("")
async def create_policy(data: PolicyCreate, request: Request, db: Session = Depends(db_with_tenant)):
    tid = tenant_id(request)
    if data.application_id:
        app = db.query(Application).filter(Application.id == data.application_id, Application.tenant_id == tid).first()
        if not app:
            raise HTTPException(status_code=404, detail="Application not found for tenant")
    actor = _actor_id(request)
    now = datetime.now(UTC)
    policy = Policy(
        id=str(uuid.uuid4()),
        name=data.name,
        rules=json.dumps(data.rules, sort_keys=True),
        application_id=data.application_id,
        tenant_id=tid,
        current_version=1,
        created_at=now,
    )
    db.add(policy)
    db.flush()
    db.add(PolicyVersion(
        id=str(uuid.uuid4()), policy_id=policy.id, tenant_id=tid, version=1,
        rules=policy.rules, created_by=actor, created_at=now,
    ))
    _record_audit(db, tid, actor, "policy.created", "policy", policy.id, {"version": 1})
    db.commit()
    db.refresh(policy)
    return _policy_dict(policy)


@router.get("/")
@router.get("")
async def list_policies(request: Request, db: Session = Depends(db_with_tenant)):
    tid = tenant_id(request)
    policies = db.query(Policy).filter(Policy.tenant_id == tid).order_by(Policy.created_at.desc()).all()
    return [_policy_dict(p) for p in policies]


@router.get("/{policy_id}")
async def get_policy(policy_id: str, request: Request, db: Session = Depends(db_with_tenant)):
    tid = tenant_id(request)
    policy = _get_policy(policy_id, tid, db)
    latest = _ensure_initial_version(policy, db, _actor_id(request))
    db.commit()
    return _policy_dict(policy, latest)


@router.post("/{policy_id}/versions")
async def create_policy_version(
    policy_id: str,
    data: PolicyVersionCreate,
    request: Request,
    db: Session = Depends(db_with_tenant),
):
    tid = tenant_id(request)
    policy = _get_policy(policy_id, tid, db)
    latest = _ensure_initial_version(policy, db, _actor_id(request))
    now = datetime.now(UTC)
    next_version = latest.version + 1
    latest.superseded_at = now
    policy.rules = json.dumps(data.rules, sort_keys=True)
    if data.name is not None:
        policy.name = data.name
    policy.current_version = next_version
    version = PolicyVersion(
        id=str(uuid.uuid4()), policy_id=policy.id, tenant_id=tid, version=next_version,
        rules=policy.rules, created_by=_actor_id(request), created_at=now,
    )
    db.add(version)
    _record_audit(db, tid, _actor_id(request), "policy.version.created", "policy", policy.id,
                  {"version": next_version, "previous_version": latest.version})
    db.commit()
    db.refresh(policy)
    return _policy_dict(policy, version)


@router.put("/{policy_id}")
async def update_policy(
    policy_id: str,
    data: PolicyVersionCreate,
    request: Request,
    db: Session = Depends(db_with_tenant),
):
    return await create_policy_version(policy_id, data, request, db)


@router.get("/{policy_id}/versions")
async def list_policy_versions(policy_id: str, request: Request, db: Session = Depends(db_with_tenant)):
    tid = tenant_id(request)
    policy = _get_policy(policy_id, tid, db)
    _ensure_initial_version(policy, db, _actor_id(request))
    versions = (
        db.query(PolicyVersion)
        .filter(PolicyVersion.policy_id == policy.id, PolicyVersion.tenant_id == tid)
        .order_by(PolicyVersion.version.desc())
        .all()
    )
    db.commit()
    return [
        {"id": v.id, "policy_id": v.policy_id, "version": v.version, "rules": _rules(v.rules),
         "created_by": v.created_by, "created_at": v.created_at.isoformat(),
         "rollback_of_version": v.rollback_of_version}
        for v in versions
    ]


@router.get("/{policy_id}/versions/{version}")
async def get_policy_version(policy_id: str, version: int, request: Request, db: Session = Depends(db_with_tenant)):
    tid = tenant_id(request)
    policy = _get_policy(policy_id, tid, db)
    selected = (
        db.query(PolicyVersion)
        .filter(PolicyVersion.policy_id == policy.id, PolicyVersion.tenant_id == tid,
                PolicyVersion.version == version)
        .first()
    )
    if not selected and version == 1:
        selected = _ensure_initial_version(policy, db, _actor_id(request))
        db.commit()
    if not selected:
        raise HTTPException(status_code=404, detail="Policy version not found")
    return {
        "id": selected.id, "policy_id": selected.policy_id, "version": selected.version,
        "rules": _rules(selected.rules), "created_by": selected.created_by,
        "created_at": selected.created_at.isoformat(), "active": policy.current_version == selected.version,
    }


@router.get("/{policy_id}/diff")
async def diff_policy_versions(
    policy_id: str,
    request: Request,
    from_version: int,
    to_version: int,
    db: Session = Depends(db_with_tenant),
):
    tid = tenant_id(request)
    policy = _get_policy(policy_id, tid, db)
    versions = {
        v.version: v for v in db.query(PolicyVersion).filter(
            PolicyVersion.policy_id == policy.id, PolicyVersion.tenant_id == tid,
            PolicyVersion.version.in_([from_version, to_version]),
        ).all()
    }
    for required in (from_version, to_version):
        if required not in versions:
            raise HTTPException(status_code=404, detail=f"Policy version {required} not found")
    old_text = json.dumps(_rules(versions[from_version].rules), indent=2, sort_keys=True).splitlines()
    new_text = json.dumps(_rules(versions[to_version].rules), indent=2, sort_keys=True).splitlines()
    return {
        "policy_id": policy.id,
        "from_version": from_version,
        "to_version": to_version,
        "changed": old_text != new_text,
        "diff": "\n".join(difflib.unified_diff(old_text, new_text, fromfile=f"v{from_version}", tofile=f"v{to_version}", lineterm="")),
        "from_rules": _rules(versions[from_version].rules),
        "to_rules": _rules(versions[to_version].rules),
    }


@router.post("/{policy_id}/rollback/{version}")
async def rollback_policy(
    policy_id: str,
    version: int,
    request: Request,
    body: PolicyRollback | None = None,
    db: Session = Depends(db_with_tenant),
):
    tid = tenant_id(request)
    policy = _get_policy(policy_id, tid, db)
    target = db.query(PolicyVersion).filter(
        PolicyVersion.policy_id == policy.id, PolicyVersion.tenant_id == tid,
        PolicyVersion.version == version,
    ).first()
    if not target:
        raise HTTPException(status_code=404, detail="Policy version not found")
    latest = _ensure_initial_version(policy, db, _actor_id(request))
    if latest.version == version:
        return _policy_dict(policy, latest)
    now = datetime.now(UTC)
    latest.superseded_at = now
    next_version = latest.version + 1
    policy.rules = target.rules
    policy.current_version = next_version
    restored = PolicyVersion(
        id=str(uuid.uuid4()), policy_id=policy.id, tenant_id=tid, version=next_version,
        rules=target.rules, created_by=_actor_id(request), created_at=now,
        rollback_of_version=version,
    )
    db.add(restored)
    _record_audit(db, tid, _actor_id(request), "policy.rollback", "policy", policy.id,
                  {"from_version": latest.version, "restored_version": version, "new_version": next_version,
                   "reason": body.reason if body else "manual rollback"})
    db.commit()
    db.refresh(policy)
    return _policy_dict(policy, restored)
