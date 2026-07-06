"""Low-level memory checks shared by commandlet and editor routes."""

from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path


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


def snapshot() -> dict:
    status = MemoryStatusEx()
    status.dwLength = ctypes.sizeof(MemoryStatusEx)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        return {"available": False}
    return {
        "available": True,
        "memory_load_percent": int(status.dwMemoryLoad),
        "total_physical_gb": round(status.ullTotalPhys / (1024 ** 3), 2),
        "free_physical_gb": round(status.ullAvailPhys / (1024 ** 3), 2),
        "total_pagefile_gb": round(status.ullTotalPageFile / (1024 ** 3), 2),
        "free_pagefile_gb": round(status.ullAvailPageFile / (1024 ** 3), 2),
        "total_virtual_gb": round(status.ullTotalVirtual / (1024 ** 3), 2),
        "free_virtual_gb": round(status.ullAvailVirtual / (1024 ** 3), 2),
    }


def project_root_from_env() -> Path:
    root = os.environ.get("WORLDFORGE_PROJECT_ROOT")
    if root:
        return Path(root).resolve()
    try:
        import unreal  # type: ignore

        return Path(unreal.Paths.project_dir()).resolve()
    except Exception:
        return Path.cwd().resolve()


def write_memory_profile(path: str | Path, extra: dict | None = None) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = snapshot()
    if extra:
        payload.update(extra)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out
