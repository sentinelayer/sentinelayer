#!/usr/bin/env python3
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def check_server():
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        return resp.status_code == 200
    except:
        return False

def audit_headers():
    print("\n🔍 1. Security Headers")
    try:
        resp = requests.get(BASE_URL)
        headers = resp.headers
        required = ["X-Frame-Options", "X-XSS-Protection", "X-Content-Type-Options", "Strict-Transport-Security"]
        for h in required:
            if h in headers:
                print(f"   ✅ {h}: {headers[h]}")
            else:
                print(f"   ❌ {h}: MISSING")
    except Exception as e:
        print(f"   ❌ Error: {e}")

def audit_auth():
    print("\n🔍 2. Authentication")
    try:
        resp = requests.post(f"{BASE_URL}/api/v1/auth/login", json={"email": "test@example.com", "password": "password123"})
        if resp.status_code == 200 and "access_token" in resp.json():
            print("   ✅ Login works")
            return resp.json()["access_token"]
        else:
            print("   ❌ Login failed")
            return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def audit_waf(token):
    print("\n🔍 3. WAF Protection")
    if not token:
        print("   ⚠️ Skipping WAF test (no token)")
        return
    headers = {"Authorization": f"Bearer {token}"}
    attacks = [
        ("SQL Injection", "/api/v1/orders?search=SELECT%20*%20FROM%20users"),
        ("XSS", "/api/v1/orders?q=<script>alert(1)</script>"),
        ("Path Traversal", "/api/v1/orders/../../../etc/passwd"),
    ]
    for name, path in attacks:
        resp = requests.get(f"{BASE_URL}{path}", headers=headers)
        if resp.status_code in [403, 400]:
            print(f"   ✅ {name}: Blocked ({resp.status_code})")
        else:
            print(f"   ❌ {name}: Not blocked ({resp.status_code})")

def audit_orders(token):
    print("\n🔍 4. Orders API")
    if not token:
        print("   ⚠️ Skipping orders test")
        return
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Create order
    resp = requests.post(f"{BASE_URL}/api/v1/orders/", headers=headers, json={"product_id": "test", "quantity": 1, "total_amount": 10})
    if resp.status_code == 200:
        print("   ✅ Create order: OK")
        order_id = resp.json().get("id")
        
        # Get order
        resp = requests.get(f"{BASE_URL}/api/v1/orders/{order_id}", headers=headers)
        if resp.status_code == 200:
            print("   ✅ Get order: OK")
        else:
            print(f"   ❌ Get order: {resp.status_code}")
        
        # List orders
        resp = requests.get(f"{BASE_URL}/api/v1/orders/", headers=headers)
        if resp.status_code == 200:
            print("   ✅ List orders: OK")
        else:
            print(f"   ❌ List orders: {resp.status_code}")
    else:
        print(f"   ❌ Create order: {resp.status_code}")

def main():
    print("="*60)
    print("🔐 SENTINELLAYER SECURITY AUDIT")
    print("="*60)
    
    if not check_server():
        print("❌ Server is not running!")
        print("   Please start: uvicorn src.sentinelayer.api.main_full:app --reload")
        sys.exit(1)
    
    print("✅ Server is running")
    
    audit_headers()
    token = audit_auth()
    audit_waf(token)
    audit_orders(token)
    
    print("\n" + "="*60)
    print("✅ Audit complete")
    print("="*60)

if __name__ == "__main__":
    main()
