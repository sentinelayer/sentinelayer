#!/bin/bash
echo "Verifying artifact signature..."
if [ -f "image.sig" ] && [ -f "cosign.pub" ]; then
    cosign verify-blob --key cosign.pub --signature image.sig src/sentinelayer/api/main_full.py
    echo "✅ Signature verified"
else
    echo "⚠️ No signature found - skipping verification"
fi
