from sqlalchemy.orm import Session
from src.sentinelayer.database.models import Tenant, Application, Policy
from src.sentinelayer.database import SessionLocal

class ControlPlane:
    def __init__(self):
        self.db = SessionLocal()
    
    def create_tenant(self, name: str) -> dict:
        tenant = Tenant(name=name)
        self.db.add(tenant)
        self.db.commit()
        return {"id": str(tenant.id), "name": tenant.name}
    
    def get_tenants(self) -> list:
        return [{"id": str(t.id), "name": t.name} for t in self.db.query(Tenant).all()]
