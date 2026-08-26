import pytest
import os
import subprocess
from src.sentinelayer.dr.bcp import bcp

@pytest.mark.asyncio
async def test_dr_backup():
    plan = bcp.create_dr_plan("test_plan", "Test DR plan")
    assert plan["id"] is not None

    result = bcp.execute_dr_test(plan["id"])
    assert result["status"] == "COMPLETED"
    assert result["result"]["success"] is True

@pytest.mark.asyncio
async def test_backup_restore():
    backup_path = "backups/test_backup.sql"
    os.makedirs("backups", exist_ok=True)
    result = subprocess.run([
        "pg_dump",
        "-h", os.getenv("DB_HOST", "localhost"),
        "-U", os.getenv("DB_USER", "postgres"),
        "-d", os.getenv("DB_NAME", "sentinelayer"),
        "-F", "c",
        "-f", backup_path
    ], capture_output=True)
    assert result.returncode == 0
    assert os.path.exists(backup_path)
    os.remove(backup_path)
