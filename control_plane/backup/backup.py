"""Backward-compatible import path for the backup manager."""

from control_plane.app.backup.backup import BackupManager

backup_manager = BackupManager()

__all__ = ["BackupManager", "backup_manager"]
