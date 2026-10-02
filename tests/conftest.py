import os

# The application intentionally fails closed when JWT_SECRET is absent. Tests
# need a deterministic non-production secret before modules are collected.
os.environ.setdefault("JWT_SECRET", "test-only-jwt-secret-do-not-use-in-production-32")
os.environ.setdefault("SL_ENV", "test")

import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: needs live control plane / services")


def pytest_collection_modifyitems(config, items):
    for item in items:
        path = str(item.fspath)
        if any(name in path for name in (
            "test_bola_real", "test_tenant_matrix", "test_tenant_isolation_live",
            "test_full_pipeline", "test_rls", "/adversarial/",
        )):
            item.add_marker(pytest.mark.integration)
