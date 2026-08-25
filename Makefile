.PHONY: help install test lint format docker-build docker-up docker-down clean

help:
@echo "Available commands:"
@echo "  make install      - Install dependencies"
@echo "  make test         - Run tests"
@echo "  make lint         - Run linters"
@echo "  make format       - Format code"
@echo "  make docker-build - Build Docker image"
@echo "  make docker-up    - Start Docker Compose"
@echo "  make docker-down  - Stop Docker Compose"
@echo "  make clean        - Clean cache files"

install:
pip install -e .
pip install pytest pytest-cov black isort flake8 mypy

test:
pytest tests/ -v --cov=src/sentinelayer --cov-report=html

lint:
flake8 src/sentinelayer
mypy src/sentinelayer --ignore-missing-imports

format:
black src/sentinelayer tests
isort src/sentinelayer tests

docker-build:
docker build -t sentinelayer:latest .

docker-up:
docker-compose up -d
@echo "Services started. API: http://localhost:8000"
@echo "Prometheus: http://localhost:9090"
@echo "Grafana: http://localhost:3000 (admin/admin)"

docker-down:
docker-compose down

docker-logs:
docker-compose logs -f

clean:
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
rm -rf .pytest_cache .coverage htmlcov
rm -rf test_rls.db *.db

dev:
uvicorn src.sentinelayer.api.main_full:app --host 0.0.0.0 --port 8000 --reload

# Load testing commands
load-test-smoke:
k6 run tests/load/smoke_test.js

load-test-load:
k6 run tests/load/load_test.js

load-test-stress:
k6 run tests/load/stress_test.js

load-test-perf:
k6 run tests/load/performance_test.js

load-test-all:
./tests/load/run_tests.sh

load-test-docker:
docker-compose -f docker-compose.test.yml up -d
@echo "K6 is running. Check Grafana at http://localhost:3000 (admin/admin)"
@echo "To stop: docker-compose -f docker-compose.test.yml down"
