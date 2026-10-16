"""Webhook egress rules must hold at registration and at worker dispatch."""

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from control_plane.app.api.v1.webhooks import _validate_url
from control_plane.app.workers.webhook_delivery import _deliver


@pytest.mark.parametrize("url", [
    "http://hooks.example.test/events",
    "http://8.8.8.8/events",
])
def test_production_registration_disallows_plaintext_transport(monkeypatch, url):
    monkeypatch.setenv("SL_ENV", "production")
    with pytest.raises(HTTPException, match="Production webhook URLs require HTTPS"):
        _validate_url(url)


@pytest.mark.parametrize("url", [
    "https://user:password@hooks.example.test/events",
    "http://user@hooks.example.test/events",
])
def test_registration_rejects_credentials_in_urls(monkeypatch, url):
    monkeypatch.setenv("SL_ENV", "test")
    with pytest.raises(HTTPException, match="cannot include user credentials"):
        _validate_url(url)


def test_production_allows_credential_free_https_public_host(monkeypatch):
    monkeypatch.setenv("SL_ENV", "production")
    assert _validate_url("https://hooks.example.test/events") == "https://hooks.example.test/events"


@pytest.mark.parametrize("url", [
    "http://hooks.example.test/events",
    "https://user:password@hooks.example.test/events",
])
def test_worker_revalidates_existing_registration_before_network(monkeypatch, url):
    monkeypatch.setenv("SL_ENV", "production")
    from control_plane.app.workers import webhook_delivery

    def unreachable(*_args):
        raise AssertionError("worker must reject before DNS or network activity")

    monkeypatch.setattr(webhook_delivery, "_resolve_public_addresses", unreachable)
    delivery = SimpleNamespace(id="test-delivery", payload="{}")
    webhook = SimpleNamespace(url=url, secret_ciphertext="ciphertext")
    with pytest.raises(ValueError, match="requires HTTPS|credentials are not permitted"):
        _deliver(delivery, webhook)


def test_local_development_http_webhook_transport_not_prohibited(monkeypatch):
    monkeypatch.setenv("SL_ENV", "test")
    assert _validate_url("http://hooks.example.test/events") == "http://hooks.example.test/events"
