"""Fail-fast validation for production runtime configuration."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

# Keep the CLI usable from any working directory.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from control_plane.app.runtime import is_production


class ConfigurationError(RuntimeError):
    pass


def validate(env: dict[str, str] | None = None) -> list[str]:
    values = os.environ if env is None else env
    production = is_production(values)
    errors: list[str] = []

    jwt = values.get("JWT_SECRET", "")
    if production and len(jwt.encode()) < 32:
        errors.append("JWT_SECRET must be at least 32 bytes in production")
    if production and not values.get("DATABASE_URL", "").strip():
        errors.append("DATABASE_URL is required in production")
    if production:
        for name in ("AUTH_DATABASE_URL", "WORKER_DATABASE_URL"):
            if not values.get(name, "").strip():
                errors.append(f"{name} is required in production")
        if values.get("SL_RUN_STARTUP_MIGRATION", "0") != "0":
            errors.append("SL_RUN_STARTUP_MIGRATION must be 0 in production; use a separate migration job")
        if values.get("MIGRATION_DATABASE_URL", "").strip():
            errors.append("Migration credentials must not be exposed to the production runtime")
    if production and not values.get("REDIS_URL", "").strip():
        errors.append("REDIS_URL is required in production")
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
        if approved and running and approved != running:
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
