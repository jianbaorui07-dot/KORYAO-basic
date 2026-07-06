"""Receipt writing utilities."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def receipt_path(project_dir: Path, name: str = "WF0009_v0.9-real_build_receipt.json") -> Path:
    return project_dir / "Saved" / "WorldForge" / "Receipts" / name


def write_receipt(project_dir: Path, receipt: dict, name: str = "WF0009_v0.9-real_build_receipt.json") -> Path:
    out = receipt_path(project_dir, name)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(receipt)
    payload.setdefault("generated_at", now_iso())
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out
