#!/usr/bin/env bash
set -euo pipefail
BASE="${CONTROL_PLANE_URL:-http://localhost:8005}"
EMAIL="mfa.smoke.$(date +%s)@example.com"
PASS="TestPass12chars!"
TENANT="tenant-mfa-$(date +%s | tail -c 6)"

echo "== register $EMAIL =="
curl -sf -X POST "$BASE/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\",\"full_name\":\"MFA Smoke\",\"tenant_id\":\"$TENANT\"}"
echo

echo "== login =="
LOGIN=$(curl -sf -X POST "$BASE/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}")
TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")
[[ -n "$TOKEN" ]] || { echo "login failed: $LOGIN"; exit 1; }
echo "token ok"

echo "== mfa setup =="
SETUP=$(curl -sf -X POST "$BASE/api/v1/auth/mfa/setup" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-ID: $TENANT")
SECRET=$(echo "$SETUP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('secret',''))")
[[ -n "$SECRET" ]] || { echo "mfa setup failed: $SETUP"; exit 1; }
echo "secret=$SECRET"

CODE=$(python3 -c "import pyotp; print(pyotp.TOTP('$SECRET').now())")
echo "== mfa verify code=$CODE =="
curl -sf -X POST "$BASE/api/v1/auth/mfa/verify" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-ID: $TENANT" \
  -H "Content-Type: application/json" \
  -d "{\"code\":\"$CODE\"}"
echo

CODE2=$(python3 -c "import pyotp; print(pyotp.TOTP('$SECRET').now())")
LOGIN2=$(curl -sf -X POST "$BASE/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\",\"mfa_code\":\"$CODE2\"}")
TOKEN2=$(echo "$LOGIN2" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")
[[ -n "$TOKEN2" ]] || { echo "mfa login failed: $LOGIN2"; exit 1; }
echo "mfa login ok"
echo "== SMOKE MFA PASSED =="
