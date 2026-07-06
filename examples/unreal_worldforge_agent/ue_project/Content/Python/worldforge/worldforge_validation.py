"""Validation report generation for WorldForge."""

from __future__ import annotations

import json
from pathlib import Path

from . import worldforge_asset_registry as registry


def validate_filesystem(project_dir: Path) -> dict:
    status = registry.filesystem_asset_status(project_dir)
    missing = [package for package, item in status.items() if not item["exists"]]
    return {
        "scope": "filesystem",
        "required_count": len(status),
        "missing_count": len(missing),
        "missing": missing,
        "assets": status,
        "complete": len(missing) == 0,
    }


def validate_unreal_assets() -> dict:
    status = registry.unreal_asset_status()
    missing = [package for package, item in status.items() if not item.get("exists")]
    return {
        "scope": "unreal_asset_registry",
        "required_count": len(status),
        "missing_count": len(missing),
        "missing": missing,
        "assets": status,
        "complete": len(missing) == 0,
    }


def write_validation(project_dir: Path, report: dict, name: str = "WF0009_v0.9-real_validation.json") -> Path:
    out_dir = project_dir / "Saved" / "WorldForge" / "Receipts"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / name
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path
