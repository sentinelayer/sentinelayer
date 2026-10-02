"""Provision dedicated PostgreSQL service roles using migration-owned credentials.

Run after Alembic migrations. This changes grants/policies in a dedicated
SentinelLayer database; never run it against a database shared with other apps.
Passwords are supplied by the platform and are never printed.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import psycopg2
from psycopg2 import sql
from control_plane.app.infrastructure.db.models import Base

ROLES = {"runtime": "sentinel_app", "authentication": "sentinel_auth", "worker": "sentinel_worker"}
AUTH_TABLES = {"tenants", "users", "auth_sessions", "api_keys", "bootstrap_admin_grants"}
WORKER_GRANTS = {
    "evidence": "SELECT, UPDATE", "offboarding_requests": "SELECT, UPDATE",
    "legal_holds": "SELECT", "applications": "SELECT, DELETE", "policies": "SELECT, DELETE",
    "policy_versions": "SELECT, DELETE", "audit_events": "SELECT, INSERT",
    "webhook_registrations": "SELECT", "webhook_deliveries": "SELECT, UPDATE",
}


def configure_roles(connection, passwords: dict[str, str]) -> None:
    tables = set(Base.metadata.tables)
    with connection.cursor() as cursor:
        cursor.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
        for profile, name in ROLES.items():
            secret = passwords[profile]
            if len(secret) < 24:
                raise ValueError(f"{profile} database password must be at least 24 characters")
            role = sql.Identifier(name)
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (name,))
            if not cursor.fetchone():
                cursor.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(role))
            cursor.execute(sql.SQL("ALTER ROLE {} LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD {}").format(role, sql.Literal(secret)))
            cursor.execute(sql.SQL("ALTER ROLE {} SET row_security = on").format(role))
            cursor.execute("SELECT current_database()")
            database = cursor.fetchone()[0]
            cursor.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(sql.Identifier(database), role))
            cursor.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(role))
            cursor.execute(sql.SQL("REVOKE ALL ON ALL TABLES IN SCHEMA public FROM {}").format(role))
            cursor.execute(sql.SQL("REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM {}").format(role))
            if profile == "runtime":
                grants = {table: "SELECT, INSERT, UPDATE, DELETE" for table in tables if table != "bootstrap_admin_grants"}
                grants["audit_events"] = "SELECT, INSERT"
            elif profile == "authentication":
                grants = {table: "SELECT, INSERT, UPDATE" for table in AUTH_TABLES}
            else:
                grants = WORKER_GRANTS
            for table, privileges in grants.items():
                cursor.execute(sql.SQL("GRANT {} ON {} TO {}").format(sql.SQL(privileges), sql.Identifier(table), role))
                if profile != "runtime" and (table == "tenants" or "tenant_id" in Base.metadata.tables[table].c):
                    policy = sql.Identifier(f"{name}_service_access")
                    cursor.execute(sql.SQL("DROP POLICY IF EXISTS {} ON {}").format(policy, sql.Identifier(table)))
                    cursor.execute(sql.SQL("CREATE POLICY {} ON {} TO {} USING (true) WITH CHECK (true)").format(policy, sql.Identifier(table), role))
    connection.commit()


def main():
    url = os.environ["MIGRATION_DATABASE_URL"]
    passwords = {profile: os.environ[f"{profile.upper()}_DATABASE_PASSWORD"] for profile in ROLES}
    with psycopg2.connect(url) as connection:
        configure_roles(connection, passwords)
    print("Dedicated database role grants configured")


if __name__ == "__main__":
    main()
