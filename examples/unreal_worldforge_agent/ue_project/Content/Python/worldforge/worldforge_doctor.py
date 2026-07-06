"""Doctor helpers for WorldForge v1.1."""

from __future__ import annotations

import json
from pathlib import Path


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def summarize_doctor(doctor_dir: str | Path) -> dict:
    root = Path(doctor_dir)
    return {
        "environment_audit": (root / "WF0009_environment_audit.json").exists(),
        "plugin_capabilities": (root / "WF0009_plugin_capabilities.json").exists(),
        "memory_profile": (root / "WF0009_memory_profile.json").exists(),
        "asset_inventory": (root / "WF0009_existing_asset_inventory.json").exists(),
        "execution_capabilities": (root / "WF0009_execution_capabilities.md").exists(),
    }
