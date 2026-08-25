from sqlalchemy import create_engine, Column, String, DateTime, func, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import os

Base = declarative_base()  # ✅ Ini yang bener

class TenantAwareMixin:
    tenant_id = Column(String(36), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    @classmethod
    def get_tenant_filter(cls, tenant_id: str):
        return cls.tenant_id == tenant_id

class DatabaseManager:
    def __init__(self, database_url: str = None):
        if not database_url:
            database_url = os.getenv(
                "DATABASE_URL",
                "sqlite:///./sentinelayer.db"
            )
        
        self.is_sqlite = database_url.startswith("sqlite")
        self.database_url = database_url
        
        if self.is_sqlite:
            self.engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False}
            )
        else:
            self.engine = create_engine(
                database_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True
            )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def get_session(self, tenant_id: str = None) -> Session:
        session = self.SessionLocal()
        if tenant_id and not self.is_sqlite:
            try:
                session.execute(
                    text("SET app.current_tenant = :tenant_id"),
                    {"tenant_id": tenant_id}
                )
            except Exception:
                pass
        return session
    
    def create_tables(self):
        Base.metadata.create_all(self.engine)
        
        if not self.is_sqlite:
            with self.engine.connect() as conn:
                for table in Base.metadata.tables:
                    try:
                        conn.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
                        conn.execute(text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY"))
                    except Exception:
                        pass
                conn.commit()
