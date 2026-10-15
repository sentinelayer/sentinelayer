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
        "AUTH_DATABASE_URL": "postgresql://auth",
        "WORKER_DATABASE_URL": "postgresql://worker",
        "SL_RUN_STARTUP_MIGRATION": "0",
        "REDIS_URL": "redis://example",
        "SL_AUTO_CREATE_SCHEMA": "0",
        "KMS_KEY": "managed-by-secret-manager",
        "SL_ENFORCE_PROVENANCE": "1",
        "SL_APPROVED_ARTIFACT_HASH": "a" * 64,
        "SL_RUNNING_ARTIFACT_HASH": "a" * 64,
    }
    assert validate(values) == []


def test_true_provenance_flag_requires_both_hashes() -> None:
    for flag in ("true", "TRUE", " true ", "1"):
        errors = validate({"SL_ENFORCE_PROVENANCE": flag})
        assert "SL_APPROVED_ARTIFACT_HASH is required when provenance enforcement is enabled" in errors
        assert "SL_RUNNING_ARTIFACT_HASH is required when provenance enforcement is enabled" in errors


def test_explicit_empty_config_does_not_use_process_environment(monkeypatch) -> None:
    monkeypatch.setenv("SL_ENFORCE_PROVENANCE", "1")
    monkeypatch.delenv("SL_APPROVED_ARTIFACT_HASH", raising=False)
    monkeypatch.delenv("SL_RUNNING_ARTIFACT_HASH", raising=False)
    assert validate({}) == []
    assert validate() != []


def test_provenance_rejects_invalid_or_mismatched_digests():
    errors = validate({"SL_ENFORCE_PROVENANCE": "true",
                      "SL_APPROVED_ARTIFACT_HASH": "z" * 64,
                      "SL_RUNNING_ARTIFACT_HASH": "z" * 64})
    assert "SL_APPROVED_ARTIFACT_HASH must be a SHA-256 hex digest" in errors
    errors = validate({"SL_ENFORCE_PROVENANCE": "1",
                      "SL_APPROVED_ARTIFACT_HASH": "a" * 64,
                      "SL_RUNNING_ARTIFACT_HASH": "b" * 64})
    assert "Running artifact does not match the approved artifact digest" in errors


def test_production_runtime_rejects_migration_credentials():
    errors = validate({"SL_ENV": "production", "MIGRATION_DATABASE_URL": "postgresql://migration",
                       "SL_RUN_STARTUP_MIGRATION": "1"})
    assert "Migration credentials must not be exposed to the production runtime" in errors
    assert "SL_RUN_STARTUP_MIGRATION must be 0 in production; use a separate migration job" in errors


def test_grant_only_restore_refuses_active_database_before_any_sql():
    from scripts.configure_database_roles import configure_roles
    class ActiveDatabase:
        def get_dsn_parameters(self): return {"dbname": "sentinelayer"}
        def cursor(self): raise AssertionError("active database SQL must not execute")
    import pytest
    with pytest.raises(ValueError, match="disposable"):
        configure_roles(ActiveDatabase(), {}, provision_roles=False)



def test_production_rejects_sqlite_or_non_postgres_database_urls() -> None:
    for bad in ("sqlite:///local.db", "http://db.example", "not-a-uri",
                "postgresql://", "postgresql://db.example:invalid/app",
                "postgresql://db.example:70000/app"):
        for field in ("DATABASE_URL", "AUTH_DATABASE_URL", "WORKER_DATABASE_URL"):
            errors = validate({"SL_ENV": "production", field: bad})
            assert f"{field} must use a valid PostgreSQL URL" in errors
            assert bad not in "\n".join(errors)


def test_production_redis_dependency_requires_redis_scheme_and_host() -> None:
    for bad in ("http://cache.example", "redis://", "localhost:6379",
                "redis://cache.example:bad", "redis://cache.example:99999"):
        errors = validate({"SL_ENV": "production", "REDIS_URL": bad})
        assert "REDIS_URL must use a valid Redis URL" in errors
        assert bad not in "\n".join(errors)


def test_production_validates_postgres_driver_and_tls_redis_schemes() -> None:
    from scripts.validate_runtime_config import valid_dependency_url, POSTGRES_SCHEMES, REDIS_SCHEMES
    for url in ("postgresql://db.example/app", "postgresql+asyncpg://db.example/app",
                "postgresql+psycopg2://db.example/app"):
        assert valid_dependency_url(url, POSTGRES_SCHEMES)
    assert valid_dependency_url("rediss://cache.example:6380/0", REDIS_SCHEMES)


def test_provenance_hash_comparison_is_case_insensitive_for_hex_digits() -> None:
    assert validate({
        "SL_ENFORCE_PROVENANCE": "true",
        "SL_APPROVED_ARTIFACT_HASH": "A" * 64,
        "SL_RUNNING_ARTIFACT_HASH": "a" * 64,
    }) == []


def test_production_rejects_unrecognized_provenance_flags() -> None:
    for value in ("yes", "tru", "enabled", "2", "off", "unexpected"):
        errors = validate({"SL_ENV": "production", "SL_ENFORCE_PROVENANCE": value})
        assert "SL_ENFORCE_PROVENANCE must be 0/false or 1/true in production" in errors


def test_known_false_provenance_flags_remain_explicitly_supported() -> None:
    for value in ("0", "false", "FALSE", " false "):
        errors = validate({"SL_ENV": "production", "SL_ENFORCE_PROVENANCE": value})
        assert "SL_ENFORCE_PROVENANCE must be 0/false or 1/true in production" not in errors
        assert "SL_APPROVED_ARTIFACT_HASH is required when provenance enforcement is enabled" not in errors
