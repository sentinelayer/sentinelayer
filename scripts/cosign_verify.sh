#!/bin/bash
echo "Verifying artifact signatures..."
if [ -f "cosign.pub" ] && [ -f "image.sig" ]; then
    cosign verify-blob --key cosign.pub --signature image.sig src/sentinelayer/api/main_full.py
    if [ $? -eq 0 ]; then
        echo "SIGNATURE VERIFIED"
    else
        echo "SIGNATURE VERIFICATION FAILED"
        exit 1
    fi
else
    echo "ERROR: cosign.pub or image.sig not found"
    exit 1
fi
