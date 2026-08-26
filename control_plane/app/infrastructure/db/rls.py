from sqlalchemy import text
from control_plane.app.infrastructure.db.session import engine

def enable_rls():
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE users ENABLE ROW LEVEL SECURITY"))
        conn.execute(text("ALTER TABLE users FORCE ROW LEVEL SECURITY"))
        conn.execute(text("""
            CREATE POLICY IF NOT EXISTS tenant_isolation_policy ON users
            USING (tenant_id = current_setting('app.current_tenant_id'))
        """))
        conn.commit()

def set_tenant_context(tenant_id: str):
    with engine.connect() as conn:
        conn.execute(text("SET app.current_tenant_id = :tenant_id"), {"tenant_id": tenant_id})
        conn.commit()

def set_user_context(user_id: str):
    with engine.connect() as conn:
        conn.execute(text("SET app.current_user_id = :user_id"), {"user_id": user_id})
        conn.commit()
