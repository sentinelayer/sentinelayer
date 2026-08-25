from sqlalchemy import create_engine, Column, String, DateTime, func, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os

Base = declarative_base()

class TenantAwareMixin:
    """Mixin untuk semua model yang perlu tenant isolation"""
    
    tenant_id = Column(String(36), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    @classmethod
    def get_tenant_filter(cls, tenant_id: str):
        """Get filter untuk tenant isolation"""
        return cls.tenant_id == tenant_id

class DatabaseManager:
    """Database manager dengan RLS support"""
    
    def __init__(self, database_url: str = None):
        if not database_url:
            database_url = os.getenv(
                "DATABASE_URL",
                "postgresql://postgres:postgres@localhost:5432/sentinelayer"
            )
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
        
        # Set tenant context untuk RLS
        if tenant_id:
            session.execute(
                text("SET app.current_tenant = :tenant_id"),
                {"tenant_id": tenant_id}
            )
            session.execute(
                text("SET app.current_user = :user_id"),
                {"user_id": "system"}
            )
        
        return session
    
    def create_tables(self):
        """Create all tables dengan RLS"""
        Base.metadata.create_all(self.engine)
        
        # Enable RLS
        with self.engine.connect() as conn:
            # Enable RLS on all tables
            for table in Base.metadata.tables:
                conn.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
                conn.execute(text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY"))
            
            # Create RLS policies
            conn.execute(text("""
                CREATE OR REPLACE FUNCTION app.current_tenant_setting()
                RETURNS text AS $$
                SELECT current_setting('app.current_tenant', true)
                $$ LANGUAGE sql;
            """))
            
            # Policy: users can only see their tenant's data
            for table in Base.metadata.tables:
                if table in ["alembic_version", "spatial_ref_sys"]:
                    continue
                conn.execute(text(f"""
                    CREATE POLICY tenant_isolation_policy ON {table}
                    USING (tenant_id = app.current_tenant_setting())
                    WITH CHECK (tenant_id = app.current_tenant_setting())
                """))
            
            conn.commit()
