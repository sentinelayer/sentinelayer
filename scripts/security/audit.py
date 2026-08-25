#!/usr/bin/env python3
"""
SentinelLayer Security Audit Script
"""

import requests
import json
import sys

def check_server():
    try:
        resp = requests.get("http://localhost:8000/health", timeout=5)
        return resp.status_code == 200
    except:
        return False

def run_audit():
    print("="*60)
    print("🔐 SENTINELLAYER SECURITY AUDIT")
    print("="*60)
    
    # Check server
    print("\n📌 Checking server status...")
    if not check_server():
        print("❌ Server is not running!")
        print("   Please start server first:")
        print("   python -m uvicorn src.sentinelayer.api.main_full:app --host 0.0.0.0 --port 8000")
        return
    
    print("✅ Server is running\n")
    
    # 1. Headers
    print("📌 1. Security Headers")
    try:
        resp = requests.get("http://localhost:8000/")
        headers = resp.headers
        checks = [
            ("X-Frame-Options", "SAMEORIGIN"),
            ("X-XSS-Protection", "1; mode=block"),
            ("X-Content-Type-Options", "nosniff"),
        ]
        for name, expected in checks:
            if name in headers:
                print(f"   ✅ {name}: {headers[name]}")
            else:
                print(f"   ❌ {name}: MISSING")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 2. JWT
    print("\n📌 2. JWT Authentication")
    try:
        resp = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"}
        )
        if resp.status_code == 200:
            token = resp.json().get("access_token")
            if token:
                print("   ✅ JWT: Working")
            else:
                print("   ❌ JWT: No token returned")
        else:
            print(f"   ❌ JWT: Login failed ({resp.status_code})")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 3. WAF
    print("\n📌 3. WAF Protection")
    try:
        # Login first
        resp = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"}
        )
        token = resp.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        attacks = [
            ("SQL Injection", "/api/v1/orders?search=SELECT%20*%20FROM%20users"),
            ("XSS", "/api/v1/orders?q=<script>alert(1)</script>"),
        ]
        for name, path in attacks:
            resp = requests.get(f"http://localhost:8000{path}", headers=headers)
            if resp.status_code == 403:
                print(f"   ✅ {name}: Blocked (403)")
            else:
                print(f"   ⚠️ {name}: Not blocked ({resp.status_code})")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "="*60)
    print("📊 AUDIT COMPLETE")
    print("="*60)

if __name__ == "__main__":
    run_audit()
