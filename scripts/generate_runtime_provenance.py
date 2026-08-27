"""Generate the runtime provenance manifest from files in the build context."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ARTIFACTS = (Path("control_plane/app/main.py"),)


def generate(root: Path) -> dict[str, object]:
    artifacts: dict[str, dict[str, object]] = {}
    for relative_path in ARTIFACTS:
        path = root / relative_path
        if not path.is_file():
            raise FileNotFoundError(f"provenance artifact not found: {relative_path}")
        artifacts[relative_path.as_posix()] = {
            "hash": hashlib.sha256(path.read_bytes()).hexdigest(),
            "verified": True,
        }
    return {"version": "1.0.0", "artifacts": artifacts}


def main() -> None:
    root = Path.cwd()
    manifest_path = root / "security/manifests/runtime-provenance.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(generate(root), indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
