#!/bin/sh
set -eu
: "${MIGRATION_DATABASE_URL:?MIGRATION_DATABASE_URL is required}"
: "${RUNTIME_DATABASE_PASSWORD:?RUNTIME_DATABASE_PASSWORD is required}"
: "${AUTHENTICATION_DATABASE_PASSWORD:?AUTHENTICATION_DATABASE_PASSWORD is required}"
: "${WORKER_DATABASE_PASSWORD:?WORKER_DATABASE_PASSWORD is required}"
cd /app
python -m alembic -c alembic.ini upgrade head
python scripts/configure_database_roles.py
