import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: needs live control plane / services")


def pytest_collection_modifyitems(config, items):
    for item in items:
        path = str(item.fspath)
        if "test_bola" in path or "test_tenant" in path or "test_security_e2e" in path or "test_dr" in path:
            item.add_marker(pytest.mark.integration)
