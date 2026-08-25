#!/bin/bash

echo "🚀 SentinelLayer Load Testing"
echo "=============================="
echo ""

# Check if k6 is installed
if ! command -v k6 &> /dev/null; then
    echo "❌ k6 is not installed. Please install it first:"
    echo "   https://k6.io/docs/get-started/installation/"
    exit 1
fi

# Check if server is running
echo "📡 Checking server status..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Server is running"
else
    echo "❌ Server is not running. Please start it first:"
    echo "   make dev"
    echo "   or"
    echo "   docker-compose up -d"
    exit 1
fi

echo ""
echo "Select test type:"
echo "  1) Smoke Test (quick validation)"
echo "  2) Load Test (simulate real traffic)"
echo "  3) Stress Test (find breaking point)"
echo "  4) Performance Test (detailed metrics)"
echo "  5) Run all tests"
echo ""
read -p "Enter choice (1-5): " choice

case $choice in
    1)
        echo ""
        echo "🔥 Running Smoke Test..."
        k6 run tests/load/smoke_test.js
        ;;
    2)
        echo ""
        echo "🔥 Running Load Test..."
        k6 run tests/load/load_test.js
        ;;
    3)
        echo ""
        echo "🔥 Running Stress Test..."
        k6 run tests/load/stress_test.js
        ;;
    4)
        echo ""
        echo "🔥 Running Performance Test..."
        k6 run tests/load/performance_test.js
        ;;
    5)
        echo ""
        echo "🔥 Running All Tests..."
        echo "--- Smoke Test ---"
        k6 run tests/load/smoke_test.js
        echo ""
        echo "--- Load Test ---"
        k6 run tests/load/load_test.js
        echo ""
        echo "--- Stress Test ---"
        k6 run tests/load/stress_test.js
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "✅ Tests completed!"
