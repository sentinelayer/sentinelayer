from sqlalchemy import text
from src.sentinelayer.database import engine
import uuid

class ControlPlane:
    def __init__(self):
        self.db = engine

    def create_tenant(self, name: str) -> dict:
        tenant_id = str(uuid.uuid4())
        with self.db.connect() as conn:
            conn.execute(
                text("INSERT INTO tenants (id, name) VALUES (:id, :name)"),
                {"id": tenant_id, "name": name}
            )
            conn.commit()
            return {"id": tenant_id, "name": name}

    def get_tenants(self) -> list:
        with self.db.connect() as conn:
            result = conn.execute(text("SELECT id, name FROM tenants"))
            return [{"id": r[0], "name": r[1]} for r in result]

control_plane = ControlPlane()
