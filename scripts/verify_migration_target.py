"""Guard one-shot production migrations against a wrong project or DB target.

This check runs before Alembic, with no SQL writes and no secrets in errors.
"""
from __future__ import annotations

import os
from urllib.parse import urlsplit

PROJECT_ID = "3e48d8a1-2ade-4cd9-b089-de6185771686"
ENVIRONMENT_ID = "72807016-df01-437c-8a19-97e7cf303370"


def validate(env: dict[str, str] | None = None) -> list[str]:
    values = os.environ if env is None else env
    errors: list[str] = []
    if values.get("RAILWAY_PROJECT_ID") != PROJECT_ID or values.get("RAILWAY_ENVIRONMENT_ID") != ENVIRONMENT_ID:
        errors.append("MIGRATION_RAILWAY_TARGET_MISMATCH")
    if values.get("SL_ENV") != "production":
        errors.append("MIGRATION_REQUIRES_PRODUCTION_ENVIRONMENT")
    url = values.get("MIGRATION_DATABASE_URL", "")
    try:
        parsed = urlsplit(url)
        _ = parsed.port
        if (parsed.scheme not in {"postgresql", "postgresql+psycopg2"}
                or not parsed.hostname or not parsed.username or not parsed.password
                or not parsed.path.strip("/") or parsed.fragment):
            errors.append("MIGRATION_DATABASE_URL_INVALID")
        # The dedicated Railway Postgres service must be addressed over private networking.
        elif not parsed.hostname.endswith(".railway.internal"):
            errors.append("MIGRATION_DATABASE_MUST_BE_RAILWAY_PRIVATE")
    except ValueError:
        errors.append("MIGRATION_DATABASE_URL_INVALID")
    for profile in ("RUNTIME", "AUTHENTICATION", "WORKER"):
        value = values.get(profile + "_DATABASE_PASSWORD", "")
        if len(value) < 24 or not value.isascii() or any(c.isspace() for c in value):
            errors.append(profile + "_DATABASE_PASSWORD_INVALID")
    passwords = [values.get(n + "_DATABASE_PASSWORD", "") for n in ("RUNTIME", "AUTHENTICATION", "WORKER")]
    if all(passwords) and len(set(passwords)) != len(passwords):
        errors.append("MIGRATION_SERVICE_PASSWORDS_MUST_DIFFER")
    return errors


def main() -> int:
    errors = validate()
    for error in errors:
        print(error)
    if not errors:
        print("MIGRATION_TARGET_VALIDATED")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
