"""Recovery policy definitions for WorldForge launcher scripts."""

from __future__ import annotations

from pathlib import Path
from typing import Any


RECOVERY_LOG = Path(r"<WORLDFORGE_RUNTIME>\Logs\worldforge_process_recovery.json")
WORLD_FORGE_KEYWORDS = [
    "WorldForge",
    "WF0009",
    "WF0010",
    "UnrealEditor",
    "UnrealEditor-Cmd",
    "04_WorldForge",
]


def power_shell_stop_policy() -> dict[str, Any]:
    return {
        "requires_worldforge_command_line": True,
        "requires_no_unreal_child_process": True,
        "min_age_minutes": 5,
        "min_working_set_gb": 1,
        "forbid_force": True,
        "forbid_taskkill": True,
        "recovery_log": str(RECOVERY_LOG),
        "keywords": WORLD_FORGE_KEYWORDS,
    }


def recovery_receipt(process: dict[str, Any], action: str, result: str) -> dict[str, Any]:
    return {
        "policy": power_shell_stop_policy(),
        "process": process,
        "action": action,
        "result": result,
    }
