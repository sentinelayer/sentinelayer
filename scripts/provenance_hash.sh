#!/usr/bin/env bash
# Compute artifact hash for runtime provenance (SL_RUNNING_ARTIFACT_HASH)
set -euo pipefail
TARGET="${1:-dist/gateway}"
if [[ ! -f "$TARGET" ]]; then
  echo "usage: $0 <binary-path>" >&2
  echo "file not found: $TARGET" >&2
  exit 1
fi
HASH=$(sha256sum "$TARGET" | awk '{print $1}')
echo "SL_APPROVED_ARTIFACT_HASH=$HASH"
echo "SL_RUNNING_ARTIFACT_HASH=$HASH"
echo "# export these before starting gateway with SL_ENFORCE_PROVENANCE=1"
