#!/bin/bash
echo "Rollback WAF to previous version"
cp src/sentinelayer/gateway/waf.py.bak src/sentinelayer/gateway/waf.py 2>/dev/null || echo "No backup found"
exit 0
