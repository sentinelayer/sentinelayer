from sqlalchemy.orm import Session
from src.sentinelayer.database import SessionLocal
from src.sentinelayer.database.models import Tenant, Application, Policy
import uuid

class ControlPlane:
    def __init__(self):
        self.db = SessionLocal()
    
    def create_tenant(self, name: str) -> dict:
        tenant = Tenant(id=str(uuid.uuid4()), name=name)
        self.db.add(tenant)
        self.db.commit()
        return {"id": tenant.id, "name": tenant.name}
    
    def get_tenants(self) -> list:
        return [{"id": t.id, "name": t.name} for t in self.db.query(Tenant).all()]
    
    def create_application(self, tenant_id: str, name: str) -> dict:
        app = Application(id=str(uuid.uuid4()), tenant_id=tenant_id, name=name)
        self.db.add(app)
        self.db.commit()
        return {"id": app.id, "name": app.name}
    
    def create_policy(self, application_id: str, rules: dict) -> dict:
        policy = Policy(id=str(uuid.uuid4()), application_id=application_id, rules=rules)
        self.db.add(policy)
        self.db.commit()
        return {"id": policy.id, "rules": policy.rules}

control_plane = ControlPlane()
