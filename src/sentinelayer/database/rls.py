from sqlalchemy import text
from src.sentinelayer.database import engine

def enable_rls():
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE users ENABLE ROW LEVEL SECURITY"))
        conn.execute(text("ALTER TABLE users FORCE ROW LEVEL SECURITY"))
        conn.execute(text("""
            CREATE POLICY IF NOT EXISTS users_isolation_policy ON users
            USING (
                current_setting('app.current_tenant_id', TRUE) = tenant_id::text
                OR 
                current_setting('app.current_user_id', TRUE) IN (
                    SELECT id::text FROM users WHERE is_admin = TRUE
                )
            )
        """))
        conn.commit()

def set_current_tenant(tenant_id: str):
    with engine.connect() as conn:
        conn.execute(text(f"SET app.current_tenant_id TO '{tenant_id}'"))
        conn.commit()

def set_current_user(user_id: str):
    with engine.connect() as conn:
        conn.execute(text(f"SET app.current_user_id TO '{user_id}'"))
        conn.commit()
