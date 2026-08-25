import pytest
from sentinelayer.backend.internal.auth.jwt_handler import create_token, verify_token, TokenPayload

def test_create_token():
    token = create_token({"sub": "user-123", "tenant_id": "tenant-acme"})
    assert token.startswith("fake-token-")

def test_verify_token():
    token = create_token({"sub": "user-123", "tenant_id": "tenant-acme"})
    payload = verify_token(token)
    assert payload is not None
    assert payload.sub == "user-123"
    assert payload.tenant_id == "tenant-acme"

def test_invalid_token():
    payload = verify_token("invalid-token")
    assert payload is None
