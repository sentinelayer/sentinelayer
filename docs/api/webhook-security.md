# Webhook Security

## Security Requirements
- HMAC-SHA256 signature
- Timestamp validation (5 min TTL)
- Nonce validation
- Retry with backoff
- DLQ on failure
- Destination validation

## Signature Header

## Verification Flow
1. Extract signature from header
2. Verify HMAC with secret
3. Validate timestamp not expired
4. Check nonce not used before
5. Process webhook
