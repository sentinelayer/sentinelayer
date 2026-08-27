#!/usr/bin/env bash
set -euo pipefail

artifact="${1:?usage: sign_artifacts.sh ARTIFACT [OUTPUT_PREFIX]}"
prefix="${2:-${artifact}}"
command -v cosign >/dev/null 2>&1 || { echo "cosign is required" >&2; exit 1; }
test -f "$artifact" || { echo "artifact not found: $artifact" >&2; exit 1; }

cosign sign-blob --yes \
  --output-signature "${prefix}.sig" \
  --output-certificate "${prefix}.pem" \
  "$artifact"

sha256sum "$artifact" > "${prefix}.sha256"
echo "Signed artifact: $artifact"
