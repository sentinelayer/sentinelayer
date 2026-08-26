from sqlalchemy.orm import Session
from src.sentinelayer.database import SessionLocal
import uuid

class ControlPlane:
    def __init__(self):
        self.db = SessionLocal()
    
    def create_tenant(self, name: str) -> dict:
        # Sementara pake raw SQL karna model Tenant belum ada
        with self.db.bind.connect() as conn:
            tenant_id = str(uuid.uuid4())
            conn.execute(f"INSERT INTO tenants (id, name) VALUES ('{tenant_id}', '{name}')")
            conn.commit()
            return {"id": tenant_id, "name": name}
    
    def get_tenants(self) -> list:
        with self.db.bind.connect() as conn:
            result = conn.execute("SELECT id, name FROM tenants")
            return [{"id": r[0], "name": r[1]} for r in result]

control_plane = ControlPlane()
