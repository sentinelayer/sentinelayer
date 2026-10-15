"""Fail-fast validation for production runtime configuration."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

# Keep the CLI usable from any working directory.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from control_plane.app.runtime import is_production


class ConfigurationError(RuntimeError):
    pass


def valid_dependency_url(raw: str, schemes: frozenset[str]) -> bool:
    """Reject malformed or wrong-scheme database endpoints before startup.

    Never include raw URLs in errors; they may contain database credentials.
    """
    try:
        parsed = urlsplit(raw.strip())
        _ = parsed.port  # Reject malformed or out-of-range ports.
        return (
            parsed.scheme in schemes
            and bool(parsed.hostname)
            and not parsed.fragment
        )
    except ValueError:
        return False


POSTGRES_SCHEMES = frozenset({
    "postgresql", "postgresql+psycopg2", "postgresql+psycopg", "postgresql+asyncpg",
})
REDIS_SCHEMES = frozenset({"redis", "rediss"})


def validate(env: dict[str, str] | None = None) -> list[str]:
    values = os.environ if env is None else env
    production = is_production(values)
    errors: list[str] = []

    if values.get("SL_ENGINE_WORKERS", "2") not in {"1", "2"}:
        errors.append("SL_ENGINE_WORKERS must be 1 or 2")

    if values.get("SL_ENGINE_WORKERS") == "2" and not values.get("REDIS_URL", "").strip():
        errors.append("Two engine workers require shared REDIS_URL state")

    jwt = values.get("JWT_SECRET", "")
    if production and len(jwt.encode()) < 32:
        errors.append("JWT_SECRET must be at least 32 bytes in production")
    if production:
        for name in ("DATABASE_URL", "AUTH_DATABASE_URL", "WORKER_DATABASE_URL"):
            configured = values.get(name, "").strip()
            if not configured:
                errors.append(f"{name} is required in production")
            elif not valid_dependency_url(configured, POSTGRES_SCHEMES):
                errors.append(f"{name} must use a valid PostgreSQL URL")
        if values.get("SL_RUN_STARTUP_MIGRATION", "0") != "0":
            errors.append("SL_RUN_STARTUP_MIGRATION must be 0 in production; use a separate migration job")
        if values.get("MIGRATION_DATABASE_URL", "").strip():
            errors.append("Migration credentials must not be exposed to the production runtime")
    if production:
        redis_url = values.get("REDIS_URL", "").strip()
        if not redis_url:
            errors.append("REDIS_URL is required in production")
        elif not valid_dependency_url(redis_url, REDIS_SCHEMES):
            errors.append("REDIS_URL must use a valid Redis URL")
    if production and values.get("SL_AUTO_CREATE_SCHEMA", "0") != "0":
        errors.append("SL_AUTO_CREATE_SCHEMA must be 0 in production")
    if values.get("SL_ENFORCE_PROVENANCE", "0").strip().lower() in {"1", "true"}:
        if not values.get("SL_APPROVED_ARTIFACT_HASH", "").strip():
            errors.append("SL_APPROVED_ARTIFACT_HASH is required when provenance enforcement is enabled")
        if not values.get("SL_RUNNING_ARTIFACT_HASH", "").strip():
            errors.append("SL_RUNNING_ARTIFACT_HASH is required when provenance enforcement is enabled")
        approved = values.get("SL_APPROVED_ARTIFACT_HASH", "")
        running = values.get("SL_RUNNING_ARTIFACT_HASH", "")
        for name, digest in (("SL_APPROVED_ARTIFACT_HASH", approved), ("SL_RUNNING_ARTIFACT_HASH", running)):
            if digest and not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
                errors.append(f"{name} must be a SHA-256 hex digest")
        if approved and running and approved.casefold() != running.casefold():
            errors.append("Running artifact does not match the approved artifact digest")
    if production and not values.get("KMS_KEY", "").strip():
        errors.append("KMS_KEY must be provided by the platform secret manager in production")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"configuration error: {error}", file=sys.stderr)
        return 1
    print("runtime configuration validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
