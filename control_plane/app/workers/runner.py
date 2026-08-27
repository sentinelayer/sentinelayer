"""Maintenance worker entry point for one-shot and long-running deployments."""
from __future__ import annotations

import argparse
import fcntl
import logging
import os
import signal
import time
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

import redis

from control_plane.app.workers.evidence_expiry import expire_old_evidence
from control_plane.app.workers.key_rotation import rotate_if_due
from control_plane.app.workers.offboarding_purge import purge_offboarded
from control_plane.app.workers.webhook_delivery import deliver_pending_webhooks

logger = logging.getLogger("sentinelayer.maintenance")
_STOP = False
_LOCK_KEY = "sentinellayer:maintenance:leader"
_RELEASE_SCRIPT = "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end"


def _stop(*_: object) -> None:
    global _STOP
    _STOP = True


def run_once() -> dict[str, Any]:
    jobs: dict[str, Callable[[], dict[str, Any]]] = {
        "evidence_expiry": expire_old_evidence,
        "offboarding_purge": purge_offboarded,
        "webhook_delivery": deliver_pending_webhooks,
    }
    # The legacy file-local key rotation is intentionally opt-in until it is
    # backed by the same external key lifecycle used by policy signatures.
    if os.getenv("POLICY_KEY_ROTATION_ENABLED", "0") == "1":
        jobs["key_rotation"] = rotate_if_due
    result: dict[str, Any] = {}
    for name, job in jobs.items():
        try:
            result[name] = {"ok": True, **job()}
        except Exception as exc:  # noqa: BLE001 - one failed job must not hide other maintenance results
            logger.exception("maintenance job failed: %s", name)
            result[name] = {"ok": False, "error": str(exc)}
    return result


def _redis_client() -> redis.Redis | None:
    configured_url = os.getenv("REDIS_URL", "").strip()
    if configured_url:
        return redis.Redis.from_url(configured_url, decode_responses=True)
    if os.getenv("ENVIRONMENT", "development").lower() in {"production", "prod"}:
        raise RuntimeError("REDIS_URL is required for distributed maintenance coordination in production")
    return None


@contextmanager
def _file_lock(path: str) -> Iterator[bool]:
    with open(path, "w", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
            return
        try:
            yield True
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


@contextmanager
def _redis_lease(client: redis.Redis, ttl: int) -> Iterator[bool]:
    token = uuid.uuid4().hex
    try:
        acquired = bool(client.set(_LOCK_KEY, token, nx=True, ex=ttl))
    except redis.RedisError as exc:
        raise RuntimeError("Redis is unavailable for distributed maintenance coordination") from exc
    try:
        yield acquired
    finally:
        if acquired:
            try:
                client.eval(_RELEASE_SCRIPT, 1, _LOCK_KEY, token)
            except redis.RedisError:
                logger.exception("failed to release distributed maintenance lease")


@contextmanager
def _maintenance_lease(interval: int, lock_path: str) -> Iterator[bool]:
    client = _redis_client()
    if client is not None:
        # A lease longer than a full cycle prevents a slow job from being
        # duplicated. The worker reacquires it before every cycle.
        with _redis_lease(client, max(60, interval * 2)) as acquired:
            yield acquired
        return
    with _file_lock(lock_path) as acquired:
        yield acquired


def run_forever(interval_seconds: int | None = None, lock_path: str | None = None) -> None:
    interval = interval_seconds or int(os.getenv("WORKER_INTERVAL_SECONDS", "300"))
    if interval < 10:
        raise ValueError("WORKER_INTERVAL_SECONDS must be at least 10 seconds")
    path = lock_path or os.getenv("WORKER_LOCK_PATH", "/tmp/sentinelayer-maintenance.lock")
    while not _STOP:
        started = time.monotonic()
        with _maintenance_lease(interval, path) as leader:
            if leader:
                result = run_once()
                logger.info("maintenance cycle completed: %s", result)
            else:
                logger.info("maintenance cycle skipped; another worker holds the leader lease")
        remaining = max(0.0, interval - (time.monotonic() - started))
        if remaining:
            time.sleep(remaining)


def main() -> None:
    parser = argparse.ArgumentParser(description="SentinelLayer maintenance worker")
    parser.add_argument("--once", action="store_true", help="run all jobs once and exit")
    parser.add_argument("--loop", action="store_true", help="run jobs periodically")
    parser.add_argument("--interval", type=int, default=None)
    args = parser.parse_args()
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    if args.loop:
        run_forever(args.interval)
    else:
        logger.info("maintenance cycle result: %s", run_once())


if __name__ == "__main__":
    main()
