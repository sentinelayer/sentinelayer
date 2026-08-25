import os
from sqlalchemy import create_engine, Column, String, DateTime, func
from sqlalchemy.orm import declarative_base, sessionmaker, Session

Base = declarative_base()

class TenantAwareMixin:
    """Mixin for tenant-aware models"""
    tenant_id = Column(String(36), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class DatabaseManager:
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv(
            "DATABASE_URL", 
            "sqlite:///./sentinelayer.db"
        )
        
        # Cek apakah pake SQLite
        self.is_sqlite = self.database_url.startswith("sqlite")
        
        # Engine setup (bedain SQLite vs PostgreSQL)
        if self.is_sqlite:
            self.engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False}
            )
        else:
            self.engine = create_engine(
                self.database_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True
            )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def get_session(self) -> Session:
        return self.SessionLocal()
    
    def create_tables(self):
        Base.metadata.create_all(self.engine)
        print("✅ Tables created")
    
    def drop_tables(self):
        Base.metadata.drop_all(self.engine)
        print("✅ Tables dropped")
