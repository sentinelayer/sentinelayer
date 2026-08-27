import hashlib
import json
import secrets
import uuid
from datetime import UTC, datetime

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from control_plane.app.api.deps import db_with_tenant, tenant_id
from control_plane.app.infrastructure.db.models import AuditEvent, User

router = APIRouter(prefix="/users", tags=["users"])


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    tenant_id: str | None = None
    password: str | None = None


class UserRoleUpdate(BaseModel):
    is_admin: bool


@router.post("/")
async def create_user(data: UserCreate, request: Request, db: Session = Depends(db_with_tenant)):
    caller_tenant = tenant_id(request)
    if data.tenant_id and data.tenant_id != caller_tenant:
        raise HTTPException(status_code=403, detail="Cannot create a user for another tenant")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        id=str(uuid.uuid4()),
        email=data.email,
        full_name=data.full_name,
        tenant_id=caller_tenant,
        hashed_password=bcrypt.hashpw((data.password or secrets.token_urlsafe(24)).encode(), bcrypt.gensalt()).decode(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "full_name": user.full_name, "tenant_id": caller_tenant}


@router.get("/")
async def list_users(request: Request, db: Session = Depends(db_with_tenant)):
    caller_tenant = tenant_id(request)
    users = db.query(User).filter(User.tenant_id == caller_tenant).all()
    return [
        {"id": u.id, "email": u.email, "full_name": u.full_name, "tenant_id": u.tenant_id, "is_admin": u.is_admin}
        for u in users
    ]


@router.patch("/{user_id}/role")
async def update_user_role(
    user_id: str,
    data: UserRoleUpdate,
    request: Request,
    db: Session = Depends(db_with_tenant),
):
    actor = getattr(request.state, "user_id", None)
    caller_tenant = tenant_id(request)
    target = db.query(User).filter(User.id == user_id, User.tenant_id == caller_tenant).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found for tenant")
    if target.is_admin and not data.is_admin:
        admin_count = db.query(User).filter(User.tenant_id == caller_tenant, User.is_admin.is_(True), User.is_active.is_(True)).count()
        if admin_count <= 1:
            raise HTTPException(status_code=409, detail="Cannot remove the last active tenant admin")
    target.is_admin = data.is_admin
    now = datetime.now(UTC)
    detail = json.dumps({"is_admin": data.is_admin}, sort_keys=True)
    event_id = str(uuid.uuid4())
    previous = db.query(AuditEvent).filter(AuditEvent.tenant_id == caller_tenant).order_by(
        AuditEvent.created_at.desc(), AuditEvent.id.desc()).first()
    previous_hash = previous.event_hash if previous else None
    digest = hashlib.sha256("|".join([
        previous_hash or "", caller_tenant, actor or "", "user.role.updated", "user", user_id,
        detail, now.isoformat(), event_id,
    ]).encode()).hexdigest()
    db.add(AuditEvent(
        id=event_id, tenant_id=caller_tenant, actor_id=actor, action="user.role.updated",
        resource_type="user", resource_id=user_id, detail=detail, previous_hash=previous_hash,
        event_hash=digest, created_at=now,
    ))
    db.commit()
    db.refresh(target)
    return {"id": target.id, "email": target.email, "tenant_id": target.tenant_id, "is_admin": target.is_admin}
