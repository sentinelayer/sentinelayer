# Signing key rotation and compromise

Keep policy signing, JWT authentication, gateway API keys, MFA seeds and backup
encryption keys separate. Rotating KMS_KEY currently also changes the derived
policy signer and backup encryption key; do not use it as a blind signing-key
rotation. Losing an old backup key makes its backups unrecoverable.

## Planned policy-signing rotation

1. Generate a fresh 32-byte Ed25519 seed inside the deployment secret manager.
   Store base64 in POLICY_SIGNING_PRIVATE_KEY and choose a new, unique
   POLICY_SIGNING_KEY_ID. Never print the seed or commit it.
2. Add the new public key to gateway POLICY_SIGNING_PUBLIC_KEYS_JSON **before**
   changing the control-plane signer. Keep the old key pinned during overlap.
   Re-deploy gateway and verify current policy enforcement/receipt.
3. Configure the new private signer on the control plane. Retain old public keys
   for verifying existing PolicyVersion records. Do not overwrite historical
   signatures or lower the durable gateway policy version floor.
4. Redeploy, fetch through the private service credential, verify the runtime
   envelope's key_id, signature, policy/tenant and expiry, then exercise the deny
   probe, allowed boundary, MFA and current gateway receipt. Re-run after restart.
5. Remove the old key from **gateway** trust after successful adoption and the
   60-second bundle validity window plus clock allowance. Retain historical
   verification public keys in the control plane unless their compromise requires
   explicit invalidation/re-signing of affected records. Re-test rejection of old
   runtime signatures and acceptance of new ones.
6. Record timestamps, public key IDs, deployment IDs, policy versions, receipt,
   pass/fail evidence and rollback decision. Store no private key in the record.

## Compromise

Remove compromised gateway signing trust immediately; fail-closed interruption
is preferable to accepting attacker-signed policy. Provision a fresh signer and
publish newly reviewed policy versions using surviving trusted administration.
Revoke compromised API keys and active sessions separately. Rotate JWT_SECRET
only with an explicit all-session invalidation plan. Retain old backup decryption
keys in an independently controlled recovery store and verify restoration before
retiring any encryption key. Notify affected parties through the authorized
incident process, and record scope and remediation.

Rollback restores a trusted configuration and publishes a higher policy version;
it never lowers the stored anti-rollback floor or restores compromised trust.
The local key-overlap test verifies signature mechanics, not execution of this
runbook against production.
