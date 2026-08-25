import pytest
from sentinelayer.backend.internal.auth.jwt_handler import create_token, verify_token

def test_create_token():
    token = create_token({"sub": "user-123", "tenant_id": "tenant-acme"})
    assert token is not None
    assert len(token) > 10

def test_verify_token():
    token = create_token({"sub": "user-123", "tenant_id": "tenant-acme"})
    assert token is not None

def test_invalid_token():
    payload = verify_token("invalid-token")
    assert payload is None
