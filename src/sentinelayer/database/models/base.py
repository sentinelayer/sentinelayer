from sqlalchemy import create_engine, Column, String, DateTime, func, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

class TenantAwareMixin:
    tenant_id = Column(String(36), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class DatabaseManager:
    def __init__(self, database_url: str = None):
        if not database_url:
            database_url = os.getenv(
                "DATABASE_URL",
                "postgresql://postgres:postgres@localhost:5432/sentinelayer"
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
                pool_pre_ping=True,
                pool_recycle=3600
            )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def get_session(self, tenant_id: str = None) -> Session:
        session = self.SessionLocal()
        
        # Set tenant context untuk RLS (PostgreSQL only)
        if tenant_id and not self.is_sqlite:
            try:
                session.execute(
                    text("SET app.current_tenant = :tenant_id"),
                    {"tenant_id": tenant_id}
                )
            except Exception as e:
                logger.warning(f"Could not set tenant context: {e}")
        
        return session
    
    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(self.engine)
        
        # PostgreSQL RLS setup
        if not self.is_sqlite:
            with self.engine.connect() as conn:
                # Enable RLS
                for table in Base.metadata.tables:
                    try:
                        conn.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
                        conn.execute(text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY"))
                    except Exception as e:
                        logger.warning(f"Could not enable RLS on {table}: {e}")
                
                # Create RLS function
                try:
                    conn.execute(text("""
                        CREATE OR REPLACE FUNCTION app.current_tenant_setting()
                        RETURNS text AS $$
                        SELECT current_setting('app.current_tenant', true)
                        $$ LANGUAGE sql;
                    """))
                except Exception as e:
                    logger.warning(f"Could not create RLS function: {e}")
                
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
                    except Exception as e:
                        logger.warning(f"Could not create policy on {table}: {e}")
                
                conn.commit()
                logger.info("Database tables and RLS policies created")
    
    def drop_tables(self):
        """Drop all tables"""
        Base.metadata.drop_all(self.engine)
        logger.info("All tables dropped")
