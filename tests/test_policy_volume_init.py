import os
import stat

import pytest

from scripts.prepare_policy_volume import prepare_child


def test_volume_initialization_is_private_and_preserves_state(tmp_path):
    prepare_child(str(tmp_path), os.getuid(), os.getgid())
    child = tmp_path / "runtime"
    assert stat.S_IMODE(child.stat().st_mode) == 0o700
    (child / "floor.json").write_text("stored floor")
    prepare_child(str(tmp_path), os.getuid(), os.getgid())
    assert (child / "floor.json").read_text() == "stored floor"


def test_volume_child_symlink_is_rejected(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir(mode=0o755)
    (tmp_path / "runtime").symlink_to(outside, target_is_directory=True)
    with pytest.raises(OSError):
        prepare_child(str(tmp_path), os.getuid(), os.getgid())
    assert stat.S_IMODE(outside.stat().st_mode) == 0o755
