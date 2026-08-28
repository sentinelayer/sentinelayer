from scripts.validate_runtime_config import validate


def test_development_allows_local_defaults() -> None:
    assert validate({"SL_ENV": "development", "JWT_SECRET": "short"}) == []


def test_production_requires_durable_dependencies() -> None:
    errors = validate({"SL_ENV": "production", "JWT_SECRET": "short", "SL_AUTO_CREATE_SCHEMA": "1"})
    assert "JWT_SECRET must be at least 32 bytes in production" in errors
    assert "DATABASE_URL is required in production" in errors
    assert "REDIS_URL is required in production" in errors
    assert "SL_AUTO_CREATE_SCHEMA must be 0 in production" in errors
    assert "KMS_KEY must be provided by the platform secret manager in production" in errors


def test_provenance_requires_both_hashes() -> None:
    errors = validate({"SL_ENFORCE_PROVENANCE": "1"})
    assert "SL_APPROVED_ARTIFACT_HASH is required when provenance enforcement is enabled" in errors
    assert "SL_RUNNING_ARTIFACT_HASH is required when provenance enforcement is enabled" in errors


def test_valid_production_config_passes() -> None:
    values = {
        "SL_ENV": "production",
        "JWT_SECRET": "x" * 32,
        "DATABASE_URL": "postgresql://example",
        "REDIS_URL": "redis://example",
        "SL_AUTO_CREATE_SCHEMA": "0",
        "KMS_KEY": "managed-by-secret-manager",
        "SL_ENFORCE_PROVENANCE": "1",
        "SL_APPROVED_ARTIFACT_HASH": "a" * 64,
        "SL_RUNNING_ARTIFACT_HASH": "a" * 64,
    }
    assert validate(values) == []
