from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from control_plane.app.infrastructure.db.session import get_db, set_tenant_context


def tenant_id(request: Request) -> str:
    tid = getattr(request.state, "tenant_id", None)
    if not tid:
        raise HTTPException(status_code=400, detail="Missing tenant ID")
    return tid


def db_with_tenant(request: Request, db: Session = Depends(get_db)) -> Session:
    tid = getattr(request.state, "tenant_id", None)
    if tid:
        set_tenant_context(db, tid)
    return db
