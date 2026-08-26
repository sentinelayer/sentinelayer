import pytest
import os
from control_plane.backup.backup import backup_manager

@pytest.mark.skip(reason="Requires database running")
def test_backup_and_restore():
    result = backup_manager.create_backup("test")
    assert result["success"] is True
    backup_path = result["path"]
    assert os.path.exists(backup_path)
