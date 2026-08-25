-- Enable RLS on orders table
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders FORCE ROW LEVEL SECURITY;

-- Drop existing policy if any
DROP POLICY IF EXISTS tenant_isolation_policy ON orders;

-- Create policy
CREATE POLICY tenant_isolation_policy ON orders
    USING (tenant_id = current_setting('app.current_tenant')::text)
    WITH CHECK (tenant_id = current_setting('app.current_tenant')::text);

-- Create function to set tenant context
CREATE OR REPLACE FUNCTION app.set_tenant(tenant_id text)
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_tenant', tenant_id, false);
END;
$$ LANGUAGE plpgsql;

-- Grant usage to app user
GRANT EXECUTE ON FUNCTION app.set_tenant(text) TO postgres;
