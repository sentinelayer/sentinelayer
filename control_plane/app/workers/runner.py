"""Maintenance worker entry point for one-shot and long-running deployments."""
from __future__ import annotations

import argparse
import fcntl
import logging
import os
import signal
import time
from collections.abc import Callable
from typing import Any

from control_plane.app.workers.evidence_expiry import expire_old_evidence
from control_plane.app.workers.key_rotation import rotate_if_due
from control_plane.app.workers.offboarding_purge import purge_offboarded
from control_plane.app.workers.webhook_delivery import deliver_pending_webhooks

logger = logging.getLogger("sentinelayer.maintenance")
_STOP = False


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


def run_forever(interval_seconds: int | None = None, lock_path: str | None = None) -> None:
    interval = interval_seconds or int(os.getenv("WORKER_INTERVAL_SECONDS", "300"))
    if interval < 10:
        raise ValueError("WORKER_INTERVAL_SECONDS must be at least 10 seconds")
    path = lock_path or os.getenv("WORKER_LOCK_PATH", "/tmp/sentinelayer-maintenance.lock")
    with open(path, "w", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("Another maintenance worker is already running") from exc
        while not _STOP:
            started = time.monotonic()
            result = run_once()
            logger.info("maintenance cycle completed: %s", result)
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
