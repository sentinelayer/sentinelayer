import secrets

import pytest
from cryptography.exceptions import InvalidTag

from scripts.backup_to_bucket import crypt_file


@pytest.mark.parametrize("size", [0, 1, 65535, 65536, 65537, 210000])
def test_backup_roundtrip_and_tamper_rejection(tmp_path, size):
    source, encrypted, restored = [tmp_path / name for name in ("source", "encrypted", "restored")]
    content = secrets.token_bytes(size)
    key = secrets.token_bytes(32)
    source.write_bytes(content)
    crypt_file(source, encrypted, key)
    crypt_file(encrypted, restored, key, decrypt=True)
    assert restored.read_bytes() == content
    corrupted = bytearray(encrypted.read_bytes())
    corrupted[-1] ^= 1
    encrypted.write_bytes(corrupted)
    with pytest.raises(InvalidTag):
        crypt_file(encrypted, restored, key, decrypt=True)


def test_backup_rejects_truncated_file(tmp_path):
    encrypted = tmp_path / "encrypted"
    encrypted.write_bytes(b"SLBK01")
    with pytest.raises(ValueError, match="Truncated"):
        crypt_file(encrypted, tmp_path / "restored", secrets.token_bytes(32), decrypt=True)
