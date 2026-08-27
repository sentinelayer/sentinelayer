import json
import os
import secrets
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import Any


class KeyRotationWorker:
    def __init__(self, state_path: str | None = None):
        self.rotation_interval = timedelta(hours=24)
        self.overlap = timedelta(hours=1)
        self.state_path = Path(state_path or os.getenv("POLICY_KEY_STATE", "security/private/key-rotation-state.json"))
        self._lock = Lock()
        self.keys: dict[str, Any] = self._load_state()

    def _load_state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return {"current": None, "previous": None, "previous_expires_at": None, "last_rotation": None}
        try:
            return json.loads(self.state_path.read_text())
        except (OSError, ValueError):
            return {"current": None, "previous": None, "previous_expires_at": None, "last_rotation": None}

    def _save_state(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.state_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.keys, indent=2))
        os.replace(temporary, self.state_path)

    def rotate(self) -> dict[str, Any]:
        with self._lock:
            now = datetime.now(UTC)
            self.keys = {
                "current": secrets.token_urlsafe(48),
                "previous": self.keys.get("current"),
                "previous_expires_at": (now + self.overlap).isoformat(),
                "last_rotation": now.isoformat(),
            }
            self._save_state()
            return {
                "rotated_at": self.keys["last_rotation"],
                "previous_expires_at": self.keys["previous_expires_at"],
                "key_changed": True,
            }

    def check_rotation(self) -> dict[str, Any]:
        last_raw = self.keys.get("last_rotation")
        if not last_raw:
            return {"needs_rotation": True}
        try:
            last = datetime.fromisoformat(last_raw)
        except ValueError:
            return {"needs_rotation": True}
        if last.tzinfo is None:
            last = last.replace(tzinfo=UTC)
        if datetime.now(UTC) - last >= self.rotation_interval:
            return {"needs_rotation": True}
        return {"needs_rotation": False}


def rotate_if_due(worker: KeyRotationWorker | None = None) -> dict[str, Any]:
    """Rotate persisted policy key material only when its interval has elapsed."""
    instance = worker or KeyRotationWorker()
    status = instance.check_rotation()
    if status.get("needs_rotation"):
        return {"rotated": True, **instance.rotate()}
    return {"rotated": False, **status}
