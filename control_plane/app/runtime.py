"""Shared environment detection for production security controls."""
from __future__ import annotations

import os
from collections.abc import Mapping


def is_production(env: Mapping[str, str] | None = None) -> bool:
    values = os.environ if env is None else env
    # Fail closed if either supported variable declares production, even when
    # deployment settings accidentally disagree.
    return any(values.get(key, "").strip().lower() in {"prod", "production"}
               for key in ("SL_ENV", "ENVIRONMENT"))


def runtime_environment(env: Mapping[str, str] | None = None) -> str:
    values = os.environ if env is None else env
    if is_production(values):
        return "production"
    return (values.get("SL_ENV", "").strip() or
            values.get("ENVIRONMENT", "").strip() or "development").lower()
