"""Real pg_dump/pg_restore round trip, restricted to disposable databases."""
import os
from pathlib import Path
import shutil
import subprocess
import uuid
from urllib.parse import urlsplit, urlunsplit

import psycopg2
from psycopg2 import sql
import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.integration
def test_postgres_backup_restore_round_trip(tmp_path):
    if os.getenv("TEST_POSTGRES_RESTORE") != "1":
        pytest.skip("set TEST_POSTGRES_RESTORE=1 with a disposable PostgreSQL server")
    source_url = os.environ["DATABASE_URL"]
    for program in ("pg_dump", "pg_restore"):
        assert shutil.which(program), f"{program} is required"
    suffix = uuid.uuid4().hex[:16]
    source, destination = f"sl_backup_{suffix}", f"sl_restore_{suffix}"
    parsed = urlsplit(source_url)

    def database_url(name):
        return urlunsplit(parsed._replace(path=f"/{name}"))

    admin = psycopg2.connect(source_url)
    admin.autocommit = True
    created = []
    try:
        with admin.cursor() as cursor:
            for name in (source, destination):
                cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
                created.append(name)
        with psycopg2.connect(database_url(source)) as db:
            with db.cursor() as cursor:
                cursor.execute("CREATE TABLE restore_probe (id integer PRIMARY KEY, tenant_id text NOT NULL, payload text NOT NULL)")
                cursor.execute("INSERT INTO restore_probe VALUES (1, 'tenant-a', 'before-backup'), (2, 'tenant-b', 'independent')")
        env = {**os.environ, "DATABASE_URL": database_url(source), "BACKUP_DIR": "relative-backups", "GPG_RECIPIENT": ""}
        backup = subprocess.run(["bash", str(ROOT / "scripts/backup_postgres.sh")], cwd=tmp_path, env=env,
                                text=True, capture_output=True, check=True)
        artifact = backup.stdout.strip().splitlines()[-1]
        env.update(DATABASE_URL=database_url(destination), BACKUP_FILE=artifact,
                   RESTORE_CONFIRM="I_UNDERSTAND", RESTORE_DRY_RUN="0")
        subprocess.run(["bash", str(ROOT / "scripts/restore_postgres.sh")], cwd=tmp_path, env=env,
                       text=True, capture_output=True, check=True)
        with psycopg2.connect(database_url(destination)) as db:
            with db.cursor() as cursor:
                cursor.execute("SELECT * FROM restore_probe ORDER BY id")
                assert cursor.fetchall() == [(1, "tenant-a", "before-backup"), (2, "tenant-b", "independent")]
        with (tmp_path / artifact).open("ab") as output:
            output.write(b"corrupted")
        restore = subprocess.run(["bash", str(ROOT / "scripts/restore_postgres.sh")], cwd=tmp_path, env=env,
                                 text=True, capture_output=True)
        assert restore.returncode != 0
        with psycopg2.connect(database_url(destination)) as db:
            with db.cursor() as cursor:
                cursor.execute("SELECT count(*) FROM restore_probe")
                assert cursor.fetchone() == (2,)
    finally:
        with admin.cursor() as cursor:
            for name in reversed(created):
                cursor.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))
        admin.close()


@pytest.mark.integration
def test_full_schema_restore_reapplies_grants_without_rotating_roles(tmp_path):
    if os.getenv("TEST_POSTGRES_RESTORE") != "1":
        pytest.skip("requires disposable PostgreSQL server")
    import secrets
    import sys
    from scripts.configure_database_roles import configure_roles, ROLES
    suffix = uuid.uuid4().hex
    names = ["sl_schema_" + suffix, "sentinel_restore_" + suffix]
    parsed = urlsplit(os.environ["DATABASE_URL"])
    urls = [urlunsplit(parsed._replace(path="/" + name)) for name in names]
    admin = psycopg2.connect(os.environ["DATABASE_URL"])
    admin.autocommit = True
    created = []
    try:
        with admin.cursor() as cursor:
            for name in names:
                cursor.execute(sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(sql.Identifier(name)))
                created.append(name)
        env = {**os.environ, "DATABASE_URL": urls[0], "MIGRATION_DATABASE_URL": urls[0],
               "SL_ENV": "test", "PYTHONPATH": str(ROOT)}
        subprocess.run([sys.executable, "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"],
                       cwd=ROOT, env=env, check=True, capture_output=True)
        with psycopg2.connect(urls[0]) as db:
            configure_roles(db, {profile: secrets.token_urlsafe(32) for profile in ROLES})
            with db.cursor() as cursor:
                cursor.execute("INSERT INTO tenants (id,name) VALUES ('restore-a','A'),('restore-b','B')")
                cursor.execute("INSERT INTO applications (id,name,tenant_id) VALUES ('app-a','A','restore-a'),('app-b','B','restore-b')")
        with admin.cursor() as cursor:
            cursor.execute("SELECT rolname, rolpassword FROM pg_authid WHERE rolname = ANY(%s) ORDER BY rolname", (list(ROLES.values()),))
            before = cursor.fetchall()
        dump = tmp_path / "schema.dump"
        subprocess.run(["pg_dump", "--format=custom", "--no-owner", "--no-privileges", "--dbname=" + urls[0], "--file=" + str(dump)], check=True, capture_output=True)
        subprocess.run(["pg_restore", "--no-owner", "--no-privileges", "--exit-on-error", "--single-transaction", "--dbname=" + urls[1], str(dump)], check=True, capture_output=True)
        with psycopg2.connect(urls[1]) as db:
            configure_roles(db, {}, provision_roles=False)
            with db.cursor() as cursor:
                cursor.execute("SET LOCAL ROLE sentinel_app")
                cursor.execute("SELECT id FROM applications")
                assert cursor.fetchall() == []
                cursor.execute("SELECT set_config('app.tenant_id','restore-a',true)")
                cursor.execute("SELECT id FROM applications")
                assert cursor.fetchall() == [("app-a",)]
                cursor.execute("RESET ROLE")
                cursor.execute("SET LOCAL ROLE sentinel_auth")
                cursor.execute("SELECT count(*) FROM users")
                assert cursor.fetchone() == (0,)
                cursor.execute("RESET ROLE")
                cursor.execute("SET LOCAL ROLE sentinel_worker")
                cursor.execute("SELECT count(*) FROM webhook_deliveries")
                assert cursor.fetchone() == (0,)
        with admin.cursor() as cursor:
            cursor.execute("SELECT rolname, rolpassword FROM pg_authid WHERE rolname = ANY(%s) ORDER BY rolname", (list(ROLES.values()),))
            if cursor.fetchall() != before:
                pytest.fail("Grant-only restore changed cluster-wide role credentials")
    finally:
        with admin.cursor() as cursor:
            for name in reversed(created):
                cursor.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))
        admin.close()
