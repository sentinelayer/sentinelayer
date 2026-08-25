from sqlalchemy import create_engine, Column, String, DateTime, func, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
import sys

Base = declarative_base()

class TenantAwareMixin:
    """Mixin untuk semua model yang perlu tenant isolation"""
    
    tenant_id = Column(String(36), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    @classmethod
    def get_tenant_filter(cls, tenant_id: str):
        return cls.tenant_id == tenant_id

class DatabaseManager:
    """Database manager dengan RLS support (PostgreSQL) atau app-level isolation (SQLite)"""
    
    def __init__(self, database_url: str = None):
        if not database_url:
            database_url = os.getenv(
                "DATABASE_URL",
                "sqlite:///./sentinelayer.db"  # Default SQLite buat development
            )
        
        self.is_sqlite = database_url.startswith("sqlite")
        self.database_url = database_url
        
        # Engine setup
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
        """Get session dengan tenant context"""
        session = self.SessionLocal()
        
        # Set tenant context untuk RLS (PostgreSQL only)
        if tenant_id and not self.is_sqlite:
            try:
                session.execute(
                    text("SET app.current_tenant = :tenant_id"),
                    {"tenant_id": tenant_id}
                )
            except Exception:
                pass  # Fallback jika setting ga jalan
        
        return session
    
    def create_tables(self):
        """Create all tables dengan RLS (PostgreSQL) atau app-level (SQLite)"""
        Base.metadata.create_all(self.engine)
        
        # PostgreSQL RLS setup
        if not self.is_sqlite:
            with self.engine.connect() as conn:
                # Enable RLS on all tables
                for table in Base.metadata.tables:
                    try:
                        conn.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
                        conn.execute(text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY"))
                    except Exception:
                        pass  # Skip if table doesn't exist or RLS not supported
                
                # Create RLS function
                try:
                    conn.execute(text("""
                        CREATE OR REPLACE FUNCTION app.current_tenant_setting()
                        RETURNS text AS $$
                        SELECT current_setting('app.current_tenant', true)
                        $$ LANGUAGE sql;
                    """))
                except Exception:
                    pass
                
                # Create policies
                for table in Base.metadata.tables:
                    if table in ["alembic_version", "spatial_ref_sys"]:
                        continue
                    try:
                        conn.execute(text(f"""
                            CREATE POLICY tenant_isolation_policy_{table} ON {table}
                            USING (tenant_id = app.current_tenant_setting())
                            WITH CHECK (tenant_id = app.current_tenant_setting())
                        """))
                    except Exception:
                        pass  # Policy already exists or table doesn't support RLS
                
                conn.commit()
