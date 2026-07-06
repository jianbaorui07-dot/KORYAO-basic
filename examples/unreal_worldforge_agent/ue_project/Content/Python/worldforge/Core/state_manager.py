"""Authoritative run-state handling for WorldForge.

Saved/WorldForge/run_state.json is the only source of truth. The runtime copy
is written only as a compatibility mirror.
"""

from __future__ import annotations

import ctypes
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


FRAMEWORK_VERSION = "1.0.1"
ALLOWED_PHASES = {
    "MAP_VALIDATED_PREVIEW_PENDING",
    "PREVIEW_RUNNING",
    "PREVIEW_READY",
    "EDITOR_LAUNCHING",
    "EDITOR_OPENED",
    "DONE",
    "PREVIEW_TIMEOUT",
    "PROCESS_MANUAL_INTERVENTION_REQUIRED",
    "FAILED",
    "FRAMEWORK_READY",
    "PREFLIGHT",
    "PREFLIGHT_WAITING",
    "BUILD_RUNNING",
    "BUILD_READY",
    "BUILD_SKIPPED",
    "VALIDATING",
    "VALIDATION_READY",
    "RETRY_BLOCKED",
}


def project_root() -> Path:
    env_root = os.environ.get("WORLDFORGE_PROJECT_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return Path(__file__).resolve().parents[4]


def saved_worldforge_dir(root: Path | None = None) -> Path:
    return (root or project_root()) / "Saved" / "WorldForge"


def authoritative_state_path(root: Path | None = None) -> Path:
    return saved_worldforge_dir(root) / "run_state.json"


def runtime_state_path(root: Path | None = None) -> Path:
    return (root or project_root()) / "runtime" / "run_state.json"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat()


def free_memory_gb() -> float:
    class MemoryStatusEx(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    status = MemoryStatusEx()
    status.dwLength = ctypes.sizeof(MemoryStatusEx)
    if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        return round(status.ullAvailPhys / (1024**3), 2)
    return -1.0


def c_drive_free_gb() -> float:
    return round(shutil.disk_usage("C:\\").free / (1024**3), 2)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_state(root: Path | None = None) -> dict[str, Any]:
    return read_json(authoritative_state_path(root))


def write_state(update: dict[str, Any], root: Path | None = None, mirror: bool = True) -> dict[str, Any]:
    root = root or project_root()
    path = authoritative_state_path(root)
    current = read_json(path)
    next_state = dict(current)
    next_state.update(update)
    phase = next_state.get("phase")
    if phase and phase not in ALLOWED_PHASES:
        raise ValueError(f"Unsupported WorldForge phase: {phase}")
    next_state.setdefault("framework_version", FRAMEWORK_VERSION)
    next_state["available_memory_gb"] = free_memory_gb()
    next_state["c_drive_free_gb"] = c_drive_free_gb()
    next_state["source_of_truth"] = str(path)
    next_state["updated_at"] = now_iso()
    write_json(path, next_state)
    if mirror:
        mirror_state = dict(next_state)
        mirror_state["compatibility_mirror_of"] = str(path)
        mirror_state["mirror_note"] = "Saved\\WorldForge\\run_state.json is the only authoritative state file."
        write_json(runtime_state_path(root), mirror_state)
    return next_state
