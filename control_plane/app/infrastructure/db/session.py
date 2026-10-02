import os

from fastapi import Request

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/sentinelayer",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AUTH_DATABASE_URL = os.getenv("AUTH_DATABASE_URL") or DATABASE_URL
WORKER_DATABASE_URL = os.getenv("WORKER_DATABASE_URL") or DATABASE_URL
auth_engine = engine if AUTH_DATABASE_URL == DATABASE_URL else create_engine(AUTH_DATABASE_URL, pool_pre_ping=True)
worker_engine = engine if WORKER_DATABASE_URL == DATABASE_URL else create_engine(WORKER_DATABASE_URL, pool_pre_ping=True)
AuthSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=auth_engine)
WorkerSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=worker_engine)
Base = declarative_base()


@event.listens_for(Session, "after_begin")
def _restore_tenant_context(session, transaction, connection):
    tenant = session.info.get("sentinelayer_tenant_id")
    if tenant is not None and connection.dialect.name == "postgresql":
        connection.execute(text("SELECT set_config('app.tenant_id', :tid, true)"), {"tid": tenant})


def get_db(request: Request = None):
    factory = AuthSessionLocal if request is not None and request.url.path.startswith("/api/v1/auth/") else SessionLocal
    db = factory()
    try:
        yield db
    finally:
        db.close()


def set_tenant_context(db, tenant_id: str | None) -> None:
    if not tenant_id:
        return
    # Keep the exact identity: rewriting an ID can select another tenant.
    db.info["sentinelayer_tenant_id"] = tenant_id
    # PostgreSQL uses transaction-local RLS context. SQLite has no set_config;
    # application-level tenant filters remain active for local tests.
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        if db.in_transaction():
            db.execute(text("SELECT set_config('app.tenant_id', :tid, true)"), {"tid": tenant_id})
        else:
            # after_begin sets it on this and every subsequent transaction,
            # including refresh/query calls after an endpoint commits.
            db.connection()
