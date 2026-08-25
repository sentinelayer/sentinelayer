#!/bin/bash
# OWASP ZAP Security Scan

echo "🔍 Running OWASP ZAP Security Scan..."
echo "======================================"

# Check if ZAP is installed
if ! command -v zap-cli &> /dev/null; then
    echo "❌ zap-cli not found. Installing..."
    pip install zap-cli
fi

# Setup ZAP
export ZAP_PORT=8090

# Start ZAP in background
echo "📡 Starting ZAP daemon..."
zap-cli start --port $ZAP_PORT

# Wait for ZAP to start
sleep 10

# Run active scan
echo "🔬 Running active scan on $1..."
zap-cli active-scan $1

# Generate report
echo "📊 Generating report..."
zap-cli report -o zap_report.html

# Stop ZAP
zap-cli shutdown

echo "✅ Scan complete! Report saved to zap_report.html"
