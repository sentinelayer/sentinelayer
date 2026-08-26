import os

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/sentinelayer",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def set_tenant_context(db, tenant_id: str | None) -> None:
    if not tenant_id:
        return
    safe = "".join(c for c in tenant_id if c.isalnum() or c in "-_")
    if not safe:
        return
    db.execute(text("SELECT set_config('app.tenant_id', :tid, true)"), {"tid": safe})
