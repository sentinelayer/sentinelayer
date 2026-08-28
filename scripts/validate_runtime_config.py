"""Fail-fast validation for production runtime configuration."""
from __future__ import annotations

import os
import sys


class ConfigurationError(RuntimeError):
    pass


def validate(env: dict[str, str] | None = None) -> list[str]:
    values = env or os.environ
    production = values.get("SL_ENV", values.get("ENVIRONMENT", "development")).lower() in {"prod", "production"}
    errors: list[str] = []

    jwt = values.get("JWT_SECRET", "")
    if production and len(jwt.encode()) < 32:
        errors.append("JWT_SECRET must be at least 32 bytes in production")
    if production and not values.get("DATABASE_URL", "").strip():
        errors.append("DATABASE_URL is required in production")
    if production and not values.get("REDIS_URL", "").strip():
        errors.append("REDIS_URL is required in production")
    if production and values.get("SL_AUTO_CREATE_SCHEMA", "0") == "1":
        errors.append("SL_AUTO_CREATE_SCHEMA must be 0 in production")
    if values.get("SL_ENFORCE_PROVENANCE", "0") == "1":
        if not values.get("SL_APPROVED_ARTIFACT_HASH", "").strip():
            errors.append("SL_APPROVED_ARTIFACT_HASH is required when provenance enforcement is enabled")
        if not values.get("SL_RUNNING_ARTIFACT_HASH", "").strip():
            errors.append("SL_RUNNING_ARTIFACT_HASH is required when provenance enforcement is enabled")
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
