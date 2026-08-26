# ADR 0002: Policy Signing Hierarchy

## Context
Policies need cryptographic integrity and versioning.

## Decision
Use HMAC-SHA256 for policy signing with rotation every 24 hours.

## Alternatives
- Ed25519 - more complex, slower
- No signing - insecure

## Consequences
- Simpler than asymmetric crypto
- Rotation worker handles key lifecycle
- Gateway verifies signatures
