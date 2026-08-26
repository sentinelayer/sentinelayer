.PHONY: help install dev test lint format migrate

help:
@echo "Available commands:"
@echo "  install      Install dependencies"
@echo "  dev          Run development server"
@echo "  test         Run tests"
@echo "  lint         Run linting"
@echo "  format       Format code"
@echo "  migrate      Run database migrations"

install:
pip install -e .

dev:
uvicorn src.sentinelayer.api.main:app --host 0.0.0.0 --port 8000 --reload

test:
pytest tests/ -v

lint:
flake8 src/ tests/

format:
black src/ tests/

migrate:
alembic upgrade head
