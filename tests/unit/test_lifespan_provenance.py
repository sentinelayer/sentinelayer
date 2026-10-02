from types import SimpleNamespace

import pytest

from control_plane.app import lifespan as lifecycle


@pytest.mark.asyncio
@pytest.mark.parametrize("flag", ["1", "true", "TRUE", " true "])
async def test_enabled_provenance_checks_runtime_digest(monkeypatch, flag):
    monkeypatch.setenv("SL_ENV", "test")
    monkeypatch.setenv("SL_AUTO_CREATE_SCHEMA", "0")
    monkeypatch.setenv("SL_ENFORCE_PROVENANCE", flag)
    monkeypatch.setenv("SL_APPROVED_ARTIFACT_HASH", "a" * 64)
    calls = []
    monkeypatch.setattr(lifecycle.provenance, "verify", lambda: {"verified": True})

    def verify_container(container_id, digest):
        calls.append((container_id, digest))
        return {"verified": True}

    monkeypatch.setattr(lifecycle.provenance, "verify_container", verify_container)
    monkeypatch.setattr(lifecycle, "engine", SimpleNamespace(dispose=lambda: None))
    async with lifecycle.lifespan(None):
        assert calls == [("control-plane", "a" * 64)]


@pytest.mark.asyncio
@pytest.mark.parametrize("flag", ["1", "true"])
async def test_enabled_provenance_rejects_mismatched_digest(monkeypatch, flag):
    monkeypatch.setenv("SL_ENV", "test")
    monkeypatch.setenv("SL_AUTO_CREATE_SCHEMA", "0")
    monkeypatch.setenv("SL_ENFORCE_PROVENANCE", flag)
    monkeypatch.setattr(lifecycle.provenance, "verify", lambda: {"verified": True})
    monkeypatch.setattr(
        lifecycle.provenance, "verify_container",
        lambda *_args: {"verified": False},
    )
    with pytest.raises(RuntimeError, match="Running artifact does not match"):
        async with lifecycle.lifespan(None):
            pytest.fail("Startup must reject the mismatched digest")


@pytest.mark.asyncio
@pytest.mark.parametrize("flag", ["0", "false"])
async def test_disabled_provenance_skips_digest_in_development(monkeypatch, flag):
    monkeypatch.setenv("SL_ENV", "test")
    monkeypatch.setenv("SL_AUTO_CREATE_SCHEMA", "0")
    monkeypatch.setenv("SL_ENFORCE_PROVENANCE", flag)

    def unexpected(*_args):
        pytest.fail("Disabled development provenance must not invoke verification")

    monkeypatch.setattr(lifecycle.provenance, "verify", unexpected)
    monkeypatch.setattr(lifecycle.provenance, "verify_container", unexpected)
    monkeypatch.setattr(lifecycle, "engine", SimpleNamespace(dispose=lambda: None))
    async with lifecycle.lifespan(None):
        pass


@pytest.mark.asyncio
@pytest.mark.parametrize("name", ["SL_ENV", "ENVIRONMENT"])
@pytest.mark.parametrize("value", ["prod", "production", " PROD "])
async def test_production_never_creates_schema_by_default(monkeypatch, name, value):
    monkeypatch.delenv("SL_ENV", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("SL_AUTO_CREATE_SCHEMA", raising=False)
    monkeypatch.setenv(name, value)
    monkeypatch.setenv("SL_ENFORCE_PROVENANCE", "0")
    monkeypatch.setattr(lifecycle.provenance, "verify", lambda: {"verified": True})

    def unexpected(*_args, **_kwargs):
        pytest.fail("Production must use migrations, not create_all")

    monkeypatch.setattr(lifecycle.Base.metadata, "create_all", unexpected)
    monkeypatch.setattr(lifecycle, "engine", SimpleNamespace(dispose=lambda: None))
    async with lifecycle.lifespan(None):
        pass


@pytest.mark.asyncio
async def test_production_rejects_schema_creation_before_database_access(monkeypatch):
    monkeypatch.setenv("SL_ENV", "prod")
    monkeypatch.setenv("SL_AUTO_CREATE_SCHEMA", "1")
    with pytest.raises(RuntimeError, match="SL_AUTO_CREATE_SCHEMA"):
        async with lifecycle.lifespan(None):
            pytest.fail("Startup must reject production schema creation")


@pytest.mark.asyncio
async def test_engine_is_disposed_when_application_raises(monkeypatch):
    monkeypatch.setenv("SL_ENV", "test")
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.setenv("SL_AUTO_CREATE_SCHEMA", "0")
    monkeypatch.setenv("SL_ENFORCE_PROVENANCE", "0")
    calls = []
    monkeypatch.setattr(lifecycle, "engine", SimpleNamespace(dispose=lambda: calls.append("disposed")))
    with pytest.raises(ValueError, match="application failure"):
        async with lifecycle.lifespan(None):
            raise ValueError("application failure")
    assert calls == ["disposed"]
