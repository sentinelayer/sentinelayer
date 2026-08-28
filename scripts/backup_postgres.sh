#!/usr/bin/env bash
# Create a compressed PostgreSQL backup with integrity metadata.
# Required: DATABASE_URL. Optional: BACKUP_DIR, RETENTION_DAYS, GPG_RECIPIENT.
set -Eeuo pipefail

: "${DATABASE_URL:?DATABASE_URL is required}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
mkdir -p "$BACKUP_DIR"
umask 077

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
base="$BACKUP_DIR/sentinellayer-${timestamp}.dump"
tmp="${base}.tmp"
trap 'rm -f "$tmp"' EXIT

pg_dump --format=custom --no-owner --no-privileges --dbname="$DATABASE_URL" --file="$tmp"
if [[ -n "${GPG_RECIPIENT:-}" ]]; then
  gpg --batch --yes --trust-model always --recipient "$GPG_RECIPIENT" --output "${base}.gpg" --encrypt "$tmp"
  rm -f "$tmp"
  artifact="${base}.gpg"
else
  mv "$tmp" "$base"
  artifact="$base"
fi

sha256sum "$artifact" > "${artifact}.sha256"
printf '%s\n' "$(date -u +%FT%TZ) backup=$artifact" >> "$BACKUP_DIR/backup-manifest.log"
find "$BACKUP_DIR" -type f -name 'sentinellayer-*.dump*' -mtime "+$RETENTION_DAYS" -delete
find "$BACKUP_DIR" -type f -name 'sentinellayer-*.sha256' -mtime "+$RETENTION_DAYS" -delete
printf '%s\n' "$artifact"
