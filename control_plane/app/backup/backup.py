from __future__ import annotations

import hashlib
import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.engine import make_url


_DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/sentinelayer"
_SAFE_NAME = re.compile(r"^[A-Za-z0-9_-]+$")


class BackupManager:
    def __init__(self, backup_dir: str | Path | None = None, database_url: str | None = None):
        self.backup_dir = Path(backup_dir or os.getenv("BACKUP_DIR", "backups")).resolve()
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.database_url = database_url or os.getenv("DATABASE_URL", _DEFAULT_DATABASE_URL)
        self.command_timeout = int(os.getenv("BACKUP_COMMAND_TIMEOUT_SECONDS", "900"))

    def _postgres_args(self) -> tuple[list[str], dict[str, str]]:
        url = make_url(self.database_url)
        if url.get_backend_name() != "postgresql":
            raise ValueError("BackupManager supports PostgreSQL DATABASE_URL only")
        args: list[str] = []
        if url.host:
            args += ["-h", url.host]
        if url.port:
            args += ["-p", str(url.port)]
        if url.username:
            args += ["-U", url.username]
        if url.database:
            args += ["-d", url.database]
        env = os.environ.copy()
        if url.password:
            env["PGPASSWORD"] = url.password
        return args, env

    def _inside_backup_dir(self, path: str | Path) -> Path:
        candidate = Path(path).expanduser().resolve()
        if candidate.parent != self.backup_dir:
            raise ValueError("Backup path must be directly inside the configured backup directory")
        if candidate.suffix != ".dump":
            raise ValueError("Only .dump PostgreSQL custom-format backups are accepted")
        return candidate

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def create_backup(self, backup_type: str = "full") -> dict:
        if not _SAFE_NAME.fullmatch(backup_type):
            return {"success": False, "error": "Invalid backup type"}
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"{backup_type}_{timestamp}.dump"
        try:
            db_args, env = self._postgres_args()
            result = subprocess.run(
                ["pg_dump", *db_args, "--format=custom", "--file", str(backup_path)],
                capture_output=True,
                text=True,
                env=env,
                timeout=self.command_timeout,
                check=False,
            )
            if result.returncode != 0:
                backup_path.unlink(missing_ok=True)
                return {"success": False, "error": result.stderr.strip() or "pg_dump failed"}
            return {
                "success": True,
                "path": str(backup_path),
                "timestamp": timestamp,
                "format": "postgresql-custom",
                "size": backup_path.stat().st_size,
                "sha256": self._sha256(backup_path),
            }
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            backup_path.unlink(missing_ok=True)
            return {"success": False, "error": str(exc)}

    def verify_backup(self, backup_path: str) -> dict:
        try:
            path = self._inside_backup_dir(backup_path)
            if not path.is_file():
                return {"success": False, "error": "Backup file not found"}
            db_args, env = self._postgres_args()
            result = subprocess.run(
                ["pg_restore", *db_args, "--list", str(path)],
                capture_output=True,
                text=True,
                env=env,
                timeout=self.command_timeout,
                check=False,
            )
            return {
                "success": result.returncode == 0,
                "path": str(path),
                "sha256": self._sha256(path),
                "error": result.stderr.strip() if result.returncode else None,
            }
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            return {"success": False, "error": str(exc)}

    def restore_backup(self, backup_path: str, *, allow_destructive: bool = False) -> dict:
        if not allow_destructive:
            return {"success": False, "error": "Destructive restore requires allow_destructive=True"}
        try:
            path = self._inside_backup_dir(backup_path)
            if not path.is_file():
                return {"success": False, "error": "Backup file not found"}
            verification = self.verify_backup(str(path))
            if not verification.get("success"):
                return {"success": False, "error": "Backup integrity verification failed", "verification": verification}
            db_args, env = self._postgres_args()
            result = subprocess.run(
                ["pg_restore", *db_args, "--clean", "--if-exists", "--no-owner", "--exit-on-error", "--single-transaction", str(path)],
                capture_output=True,
                text=True,
                env=env,
                timeout=self.command_timeout,
                check=False,
            )
            return {
                "success": result.returncode == 0,
                "path": str(path),
                "sha256": verification["sha256"],
                "error": result.stderr.strip() if result.returncode else None,
            }
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            return {"success": False, "error": str(exc)}

    def list_backups(self) -> list[dict]:
        backups = []
        for path in sorted(self.backup_dir.glob("*.dump"), key=lambda item: item.stat().st_mtime, reverse=True):
            backups.append({
                "path": str(path),
                "size": path.stat().st_size,
                "sha256": self._sha256(path),
                "format": "postgresql-custom",
                "modified": datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat(),
            })
        return backups
