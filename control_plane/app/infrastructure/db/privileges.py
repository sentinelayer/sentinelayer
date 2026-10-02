"""Reject database identities that can bypass the runtime security boundary."""
from sqlalchemy import text
from control_plane.app.infrastructure.db.models import Base


def validate_database_roles(runtime, authentication, worker) -> None:
    names = []
    for label, engine in (("runtime", runtime), ("authentication", authentication), ("worker", worker)):
        if engine.dialect.name != "postgresql":
            raise RuntimeError(f"{label} database must use PostgreSQL in production")
        with engine.connect() as connection:
            role = connection.execute(text("""
                SELECT current_user AS name, rolsuper, rolbypassrls, rolcreaterole, rolcreatedb,
                  EXISTS (SELECT 1 FROM pg_roles elevated
                    WHERE (elevated.rolsuper OR elevated.rolbypassrls OR elevated.rolcreaterole)
                    AND pg_has_role(current_user, elevated.oid, 'MEMBER')) AS elevated_membership
                FROM pg_roles WHERE rolname = current_user
            """)).mappings().one()
            if any(role[key] for key in ("rolsuper", "rolbypassrls", "rolcreaterole", "rolcreatedb", "elevated_membership")):
                raise RuntimeError(f"{label} database role has elevated privileges")
            owns_tables = connection.scalar(text("""
                SELECT EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                  WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p')
                  AND pg_has_role(current_user, c.relowner, 'MEMBER'))
            """))
            if owns_tables or connection.scalar(text("SELECT has_schema_privilege(current_user, 'public', 'CREATE')")):
                raise RuntimeError(f"{label} database role must not own or create application tables")
            names.append(role["name"])
    if len(set(names)) != 3:
        raise RuntimeError("Runtime, authentication and worker database roles must be distinct")
    for label, engine in (("runtime", runtime), ("authentication", authentication), ("worker", worker)):
        with engine.connect() as connection:
            for name in names:
                if name != connection.scalar(text("SELECT current_user")) and connection.scalar(
                    text("SELECT pg_has_role(current_user, :name, 'MEMBER')"), {"name": name},
                ):
                    raise RuntimeError(f"{label} database role must not inherit another service role")
    scoped = {table.name for table in Base.metadata.tables.values() if "tenant_id" in table.c} | {"tenants"}
    with runtime.connect() as connection:
        actual = dict(connection.execute(text("""
            SELECT c.relname, c.relrowsecurity FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p')
        """)).all())
    if any(actual.get(name) is not True for name in scoped):
        raise RuntimeError("Every tenant table must exist with RLS enabled before production startup")
