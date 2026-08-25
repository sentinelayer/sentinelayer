import pytest
from datetime import datetime, timedelta, timezone
from jose import jwt
from sentinelayer.backend.internal.auth.jwt_handler import (
    create_token,
    verify_token,
    TokenPayload,
    JWTConfig
)

def test_create_and_verify_token():
    # 1. Create token
    data = {
        "sub": "user-123",
        "tenant_id": "tenant-acme",
        "application_id": "payment-api",
        "session_id": "sess-xyz"
    }
    token = create_token(data, expires_delta=timedelta(minutes=5))
    
    # 2. Verify token (should succeed)
    payload = verify_token(token)
    assert payload is not None
    assert payload.sub == "user-123"
    assert payload.tenant_id == "tenant-acme"
    assert payload.application_id == "payment-api"
    assert payload.session_id == "sess-xyz"

def test_expired_token():
    # Create token with -1 minute expiry (already expired)
    data = {"sub": "user-123", "tenant_id": "tenant-acme"}
    token = create_token(data, expires_delta=timedelta(minutes=-1))
    
    # Should fail validation (expired)
    payload = verify_token(token)
    assert payload is None  # JWTError -> None

def test_invalid_token():
    # Malformed token
    payload = verify_token("this.is.not.a.jwt")
    assert payload is None

def test_missing_required_fields():
    # Create token without tenant_id (should still parse, but validation later)
    data = {"sub": "user-123"}  # missing tenant_id
    token = create_token(data)
    payload = verify_token(token)
    # TokenPayload validation will fail because tenant_id is required
    assert payload is None  # Pydantic validation error
