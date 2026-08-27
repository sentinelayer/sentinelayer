from __future__ import annotations

import pytest

from control_plane.app.workers import runner


class FakeRedis:
    def __init__(self, acquired: bool = True):
        self.acquired = acquired
        self.set_calls: list[tuple[object, ...]] = []
        self.eval_calls: list[tuple[object, ...]] = []

    def set(self, *args, **kwargs):
        self.set_calls.append((args, kwargs))
        return self.acquired

    def eval(self, *args):
        self.eval_calls.append(args)
        return 1


def test_redis_lease_releases_only_owned_token():
    client = FakeRedis()
    with runner._redis_lease(client, 60) as acquired:
        assert acquired is True
    assert client.set_calls[0][0][0] == runner._LOCK_KEY
    assert client.set_calls[0][1] == {"nx": True, "ex": 60}
    assert client.eval_calls[0][0] == runner._RELEASE_SCRIPT


def test_redis_lease_can_skip_when_another_worker_is_leader():
    client = FakeRedis(acquired=False)
    with runner._redis_lease(client, 60) as acquired:
        assert acquired is False
    assert client.eval_calls == []


def test_production_requires_redis_for_coordination(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "production")
    with pytest.raises(RuntimeError, match="REDIS_URL is required"):
        runner._redis_client()


def test_development_can_use_file_lock_fallback(monkeypatch, tmp_path):
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "development")
    lock_path = str(tmp_path / "maintenance.lock")
    with runner._maintenance_lease(60, lock_path) as leader:
        assert leader is True
