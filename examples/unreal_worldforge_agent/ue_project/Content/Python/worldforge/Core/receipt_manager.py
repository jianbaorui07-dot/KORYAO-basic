"""Receipt helpers for WorldForge runs."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from . import resource_policy, state_manager


def now_iso() -> str:
    return datetime.now().astimezone().isoformat()


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_receipt(
    name: str,
    payload: dict[str, Any],
    project_root: Path | None = None,
    runtime_copy: bool = True,
) -> dict[str, str]:
    root = project_root or state_manager.project_root()
    saved_dir = state_manager.saved_worldforge_dir(root) / "Receipts"
    saved_dir.mkdir(parents=True, exist_ok=True)
    payload = dict(payload)
    payload.setdefault("written_at", now_iso())
    saved_path = saved_dir / name
    saved_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = {"saved_receipt_path": str(saved_path)}
    if runtime_copy:
        resource_policy.RECEIPTS_PATH.mkdir(parents=True, exist_ok=True)
        runtime_path = resource_policy.RECEIPTS_PATH / name
        runtime_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        result["runtime_receipt_path"] = str(runtime_path)
    return result
