"""Exercise backup shell contracts with disposable CLI adapters, without a database."""
import os
from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def backup_commands(tmp_path):
    tools = tmp_path / "tools"
    tools.mkdir()
    dump = tools / "pg_dump"
    dump.write_text("""#!/usr/bin/env python3
import pathlib, sys
path = next(arg.split("=", 1)[1] for arg in sys.argv if arg.startswith("--file="))
pathlib.Path(path).write_bytes(b"disposable-backup-fixture")
""")
    restore = tools / "pg_restore"
    restore.write_text("""#!/usr/bin/env python3
import os, pathlib, sys
with open(os.environ["RESTORE_CALLS"], "a") as stream:
    stream.write(" ".join(sys.argv[1:]) + "\\n")
if "--list" in sys.argv:
    sys.exit(0 if pathlib.Path(sys.argv[-1]).read_bytes() == b"disposable-backup-fixture" else 1)
sys.exit(0)
""")
    dump.chmod(0o755)
    restore.chmod(0o755)
    calls = tmp_path / "restore-calls"
    env = {**os.environ, "PATH": f"{tools}:{os.environ['PATH']}",
           "DATABASE_URL": "postgresql://disposable-test",
           "RESTORE_CALLS": str(calls), "GPG_RECIPIENT": ""}
    return env, calls


@pytest.mark.parametrize("relative", [True, False])
def test_backup_checksum_can_be_restored_from_another_directory(tmp_path, backup_commands, relative):
    env, calls = backup_commands
    folder = tmp_path / "backups"
    env["BACKUP_DIR"] = "./backups" if relative else str(folder)
    created = subprocess.run(["bash", str(ROOT / "scripts/backup_postgres.sh")],
                             env=env, cwd=tmp_path, capture_output=True, text=True)
    assert created.returncode == 0, created.stderr
    artifact = next(folder.glob("*.dump"))
    env.update(BACKUP_FILE=str(artifact), RESTORE_DRY_RUN="1")
    restored = subprocess.run(["bash", str(ROOT / "scripts/restore_postgres.sh")],
                              env=env, cwd=ROOT, capture_output=True, text=True)
    assert restored.returncode == 0, restored.stderr
    assert "--list" in calls.read_text()
    artifact.write_bytes(b"corrupted")
    rejected = subprocess.run(["bash", str(ROOT / "scripts/restore_postgres.sh")],
                              env=env, cwd=ROOT, capture_output=True, text=True)
    assert rejected.returncode != 0
    assert calls.read_text().count("--list") == 1


def test_destructive_restore_uses_atomic_fail_fast_options(tmp_path, backup_commands):
    env, calls = backup_commands
    env["BACKUP_DIR"] = str(tmp_path / "backups")
    created = subprocess.run(["bash", str(ROOT / "scripts/backup_postgres.sh")],
                             env=env, capture_output=True, text=True)
    assert created.returncode == 0, created.stderr
    artifact = next((tmp_path / "backups").glob("*.dump"))
    env.update(BACKUP_FILE=str(artifact), RESTORE_CONFIRM="I_UNDERSTAND", RESTORE_DRY_RUN="0")
    restored = subprocess.run(["bash", str(ROOT / "scripts/restore_postgres.sh")],
                              env=env, capture_output=True, text=True)
    assert restored.returncode == 0, restored.stderr
    command = calls.read_text().splitlines()[-1]
    assert "--exit-on-error" in command
    assert "--single-transaction" in command
