#!/usr/bin/env bash
# Restore a PostgreSQL custom-format backup after verifying its checksum.
# Required: DATABASE_URL and BACKUP_FILE. Use RESTORE_DRY_RUN=1 to verify only.
set -Eeuo pipefail

: "${DATABASE_URL:?DATABASE_URL is required}"
: "${BACKUP_FILE:?BACKUP_FILE is required}"
[[ -f "$BACKUP_FILE" ]] || { echo "Backup not found: $BACKUP_FILE" >&2; exit 2; }

checksum_file="${BACKUP_FILE}.sha256"
[[ -f "$checksum_file" ]] || { echo "Checksum not found: $checksum_file" >&2; exit 2; }
( cd "$(dirname "$BACKUP_FILE")" && sha256sum --check "$(basename "$checksum_file")" )

input="$BACKUP_FILE"
tmp=""
cleanup() { [[ -n "$tmp" ]] && rm -f "$tmp"; }
trap cleanup EXIT
if [[ "$BACKUP_FILE" == *.gpg ]]; then
  tmp="$(mktemp --suffix=.dump)"
  gpg --batch --decrypt --output "$tmp" "$BACKUP_FILE"
  input="$tmp"
fi

pg_restore --list "$input" >/dev/null
if [[ "${RESTORE_DRY_RUN:-0}" == "1" ]]; then
  echo "Restore validation succeeded: $BACKUP_FILE"
  exit 0
fi

: "${RESTORE_CONFIRM:?Set RESTORE_CONFIRM=I_UNDERSTAND to perform destructive restore}"
[[ "$RESTORE_CONFIRM" == "I_UNDERSTAND" ]] || { echo "Invalid RESTORE_CONFIRM" >&2; exit 2; }
pg_restore --clean --if-exists --no-owner --no-privileges --dbname="$DATABASE_URL" "$input"
echo "Restore completed: $BACKUP_FILE"
