import os
import sys
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/sentinelayer")

def ensure_rls():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        # Enable RLS
        conn.execute(text("ALTER TABLE orders ENABLE ROW LEVEL SECURITY;"))
        conn.execute(text("ALTER TABLE orders FORCE ROW LEVEL SECURITY;"))
        
        # Create policy
        conn.execute(text("""
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_policies WHERE policyname = 'tenant_isolation_policy'
                ) THEN
                    CREATE POLICY tenant_isolation_policy ON orders
                        USING (tenant_id = current_setting('app.current_tenant')::text)
                        WITH CHECK (tenant_id = current_setting('app.current_tenant')::text);
                END IF;
            END $$;
        """))
        
        # Create function
        conn.execute(text("""
            CREATE OR REPLACE FUNCTION app.set_tenant(tenant_id text)
            RETURNS void AS $$
            BEGIN
                PERFORM set_config('app.current_tenant', tenant_id, false);
            END;
            $$ LANGUAGE plpgsql;
        """))
        
        conn.commit()
        print("RLS policies applied successfully")
        return True

if __name__ == "__main__":
    try:
        ensure_rls()
    except Exception as e:
        print(f"RLS apply failed: {e}")
        sys.exit(1)
