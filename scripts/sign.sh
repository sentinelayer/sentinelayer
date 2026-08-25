#!/bin/bash

IMAGE=$1

if [ -z "$IMAGE" ]; then
    echo "Usage: ./sign.sh <image-name>"
    exit 1
fi

# Generate key pair if not exists
if [ ! -f cosign.key ]; then
    cosign generate-key-pair
fi

# Sign the image
cosign sign --key cosign.key $IMAGE

# Verify the signature
cosign verify --key cosign.pub $IMAGE

echo "Image signed and verified: $IMAGE"
