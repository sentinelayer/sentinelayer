#!/bin/bash
echo "Signing artifacts..."
cosign sign-blob --key cosign.key control_plane/app/main.py
echo "Artifact signed"
