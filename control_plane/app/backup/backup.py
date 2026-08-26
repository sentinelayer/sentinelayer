import os
import subprocess
from datetime import datetime


class BackupManager:
    def __init__(self):
        self.backup_dir = "backups"
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self, backup_type: str = "full") -> dict:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.backup_dir}/{backup_type}_{timestamp}.sql"

        try:
            result = subprocess.run([
                "pg_dump",
                "-h", os.getenv("DB_HOST", "localhost"),
                "-U", os.getenv("DB_USER", "postgres"),
                "-d", os.getenv("DB_NAME", "sentinelayer"),
                "-F", "c",
                "-f", backup_path
            ], capture_output=True, text=True)

            if result.returncode == 0:
                return {"success": True, "path": backup_path, "timestamp": timestamp}
            return {"success": False, "error": result.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def restore_backup(self, backup_path: str) -> dict:
        try:
            result = subprocess.run([
                "pg_restore",
                "-h", os.getenv("DB_HOST", "localhost"),
                "-U", os.getenv("DB_USER", "postgres"),
                "-d", os.getenv("DB_NAME", "sentinelayer"),
                "--clean",
                backup_path
            ], capture_output=True, text=True)

            if result.returncode == 0:
                return {"success": True}
            return {"success": False, "error": result.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_backups(self) -> list[dict]:
        backups = []
        if not os.path.exists(self.backup_dir):
            return backups

        for f in os.listdir(self.backup_dir):
            if f.endswith(".sql"):
                path = os.path.join(self.backup_dir, f)
                backups.append({
                    "path": path,
                    "size": os.path.getsize(path),
                    "modified": datetime.fromtimestamp(os.path.getmtime(path)).isoformat()
                })
        return sorted(backups, key=lambda x: x["modified"], reverse=True)
