from __future__ import annotations

from pathlib import Path

from control_plane.app.backup.backup import BackupManager


class _Result:
    def __init__(self, returncode: int = 0, stderr: str = ""):
        self.returncode = returncode
        self.stderr = stderr
        self.stdout = "toc"


def test_backup_verify_and_restore_are_integrity_checked(tmp_path, monkeypatch):
    manager = BackupManager(tmp_path, "postgresql://user:password@db:5432/sentinelayer")

    def fake_run(command, **kwargs):
        if command[0] == "pg_dump":
            output = Path(command[command.index("--file") + 1])
            output.write_bytes(b"valid custom dump")
        return _Result()

    monkeypatch.setattr("control_plane.app.backup.backup.subprocess.run", fake_run)
    created = manager.create_backup("test")
    assert created["success"] is True
    assert len(created["sha256"]) == 64
    verified = manager.verify_backup(created["path"])
    assert verified["success"] is True
    assert verified["sha256"] == created["sha256"]
    assert manager.restore_backup(created["path"])["success"] is False
    restored = manager.restore_backup(created["path"], allow_destructive=True)
    assert restored["success"] is True


def test_backup_rejects_paths_outside_backup_directory(tmp_path):
    manager = BackupManager(tmp_path, "postgresql://user:password@db:5432/sentinelayer")
    outside = tmp_path.parent / "outside.dump"
    outside.write_bytes(b"not accepted")
    result = manager.verify_backup(str(outside))
    assert result["success"] is False
    assert "inside" in result["error"]
