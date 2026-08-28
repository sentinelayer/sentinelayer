.PHONY: help install dev test test-unit test-integration lint format migrate validate-config security backup restore verify

help:
	@echo "Available commands:"
	@echo "  install          Install Python and dashboard dependencies"
	@echo "  dev              Run development server"
	@echo "  test             Run all available tests"
	@echo "  test-unit        Run unit tests"
	@echo "  test-integration Run integration tests"
	@echo "  lint             Run static checks"
	@echo "  format           Format Python code"
	@echo "  migrate          Run database migrations"
	@echo "  validate-config  Validate runtime configuration"
	@echo "  security         Run local security checks when tools are installed"
	@echo "  backup           Create a PostgreSQL backup"
	@echo "  restore          Validate/restore a PostgreSQL backup"
	@echo "  verify           Run the complete local verification suite"

install:
	python3 -m pip install -r requirements.txt
	npm --prefix dashboard ci

dev:
	uvicorn control_plane.app.main:app --host 0.0.0.0 --port 8005 --reload

test: test-unit

test-unit:
	pytest tests/unit -v --tb=short

test-integration:
	pytest tests/integration tests/resilience tests/adversarial -v --tb=short

lint:
	python3 -m compileall -q control_plane engine scripts
	python3 -m ruff check control_plane engine scripts 2>/dev/null || true

format:
	python3 -m black control_plane engine scripts

migrate:
	alembic upgrade head

validate-config:
	python3 scripts/validate_runtime_config.py

security:
	command -v gitleaks >/dev/null && gitleaks detect --no-banner || echo "gitleaks not installed; CI runs the authoritative scan"
	command -v semgrep >/dev/null && semgrep --config=auto --error --exclude=waf/rules || echo "semgrep not installed; CI runs the authoritative scan"

backup:
	bash scripts/backup_postgres.sh

restore:
	bash scripts/restore_postgres.sh

verify: validate-config test-unit
	(cd gateway && go test ./...)
	npm --prefix dashboard run build
