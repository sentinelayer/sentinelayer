#!/bin/bash
# Nmap Security Scan

echo "🔍 Running Nmap Security Scan..."
echo "================================="

if ! command -v nmap &> /dev/null; then
    echo "❌ nmap not found. Please install: sudo apt-get install nmap"
    exit 1
fi

# Scan localhost
nmap -sV -p- --script=vuln localhost > nmap_report.txt

echo "✅ Scan complete! Report saved to nmap_report.txt"
