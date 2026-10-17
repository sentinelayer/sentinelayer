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


def test_replay_helpers_reject_empty_and_duplicate_identifiers():
    helper = WebhookSecurity(secret="a-long-test-replay-secret-of-at-least-32-bytes")
    for invalid in ("", "  ", "bad\nnewline", "x" * 257, None, 100):
        assert helper.verify_nonce(invalid) is False
        assert helper.verify_replay(invalid) is False
    assert helper.verify_nonce("nonce-1") is True
    assert helper.verify_nonce("nonce-1") is False
    assert helper.verify_replay("request-1") is True
    assert helper.verify_replay("request-1") is False


def test_local_replay_memory_rejects_new_ids_when_full_without_evicting(monkeypatch):
    helper = WebhookSecurity(secret="a-long-test-replay-secret-of-at-least-32-bytes")
    monkeypatch.setattr(helper, "MAX_RECENT_IDENTIFIERS", 2)
    assert helper.verify_nonce("nonce-1")
    assert helper.verify_nonce("nonce-2")
    assert not helper.verify_nonce("nonce-3")
    assert not helper.verify_nonce("nonce-1")
    assert set(helper.nonce_cache) == {"nonce-1", "nonce-2"}


def test_signature_verification_rejects_invalid_untrusted_types():
    helper = WebhookSecurity(secret="a-long-test-replay-secret-of-at-least-32-bytes")
    for invalid in (None, 12, b"x", "", "a" * 65):
        assert helper.verify_signature("payload", invalid) is False
