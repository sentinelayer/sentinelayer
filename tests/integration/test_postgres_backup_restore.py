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
