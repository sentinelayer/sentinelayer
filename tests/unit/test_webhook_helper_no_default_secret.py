"""Legacy in-process webhook helper never accepts a built-in signing key."""

from datetime import datetime, timedelta, timezone

import pytest

from control_plane.app.domain.webhook.security import WebhookSecurity


def test_secret_is_required_and_is_never_a_default(monkeypatch):
    monkeypatch.delenv("WEBHOOK_SECRET", raising=False)
    with pytest.raises(ValueError, match="WEBHOOK_SECRET_REQUIRED"):
        WebhookSecurity()
    with pytest.raises(ValueError, match="WEBHOOK_SECRET_REQUIRED"):
        WebhookSecurity(secret="weak-key")


def test_valid_explicit_secret_signs_and_rejects_modified_payload():
    helper = WebhookSecurity(secret="a-realistic-test-secret-with-32-plus-bytes")
    signature = helper.generate_signature('{"ok":true}')
    assert helper.verify_signature('{"ok":true}', signature)
    assert not helper.verify_signature('{"ok":false}', signature)


def test_expiration_rejects_naive_and_future_timestamps():
    helper = WebhookSecurity(secret="another-long-test-secret-value-32-bytes")
    now = datetime.now(timezone.utc)
    assert not helper.is_expired((now - timedelta(seconds=2)).isoformat())
    assert helper.is_expired((now + timedelta(days=1)).isoformat())
    assert helper.is_expired((now - timedelta(hours=1)).isoformat())
    assert helper.is_expired(now.replace(tzinfo=None).isoformat())
    assert helper.is_expired("invalid")
    assert helper.is_expired(now.isoformat(), ttl_seconds=0)
