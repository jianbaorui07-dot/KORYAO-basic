"""Resource and project checks for WorldForge editor automation."""

from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path


def import_unreal():
    try:
        import unreal  # type: ignore
    except Exception:
        return None
    return unreal


def get_project_dir() -> Path:
    env_root = os.environ.get("WORLDFORGE_PROJECT_ROOT")
    if env_root:
        return Path(env_root).resolve()
    unreal = import_unreal()
    if unreal is not None:
        return Path(unreal.Paths.project_dir()).resolve()
    return Path.cwd().resolve()


def get_free_memory_gb() -> float:
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
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        return -1.0
    return round(status.ullAvailPhys / (1024 ** 3), 2)


def load_resource_policy(project_dir: Path | None = None) -> dict:
    root = project_dir or get_project_dir()
    path = root / "Saved" / "WorldForge" / "System" / "resource_policy.json"
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_resource_mode(policy: dict, free_memory_gb: float | None = None) -> dict:
    free = get_free_memory_gb() if free_memory_gb is None else free_memory_gb
    if free < 0:
        return {"mode": "unknown", "allowed": False, "free_memory_gb": free}
    if free < policy["modes"]["build"]["free_memory_gb_min"]:
        return {
            "mode": "eco_build",
            "allowed": False,
            "free_memory_gb": free,
            "reason": "Free physical memory is below the 7 GB Build threshold.",
            "required_free_memory_gb": policy["modes"]["build"]["free_memory_gb_min"],
        }
    if free < policy["modes"]["pie_verify"]["free_memory_gb_min"]:
        return {"mode": "build", "allowed": True, "free_memory_gb": free}
    if free < policy["modes"]["cinematic_render"]["free_memory_gb_min"]:
        return {"mode": "pie_verify", "allowed": True, "free_memory_gb": free}
    return {"mode": "cinematic_render", "allowed": True, "free_memory_gb": free}


def probe_project(project_dir: Path | None = None) -> dict:
    root = project_dir or get_project_dir()
    uprojects = sorted(root.glob("*.uproject"))
    engine_root = Path("<UE_5_2_ROOT>")
    editor = engine_root / "Engine/Binaries/Win64/UnrealEditor.exe"
    editor_cmd = engine_root / "Engine/Binaries/Win64/UnrealEditor-Cmd.exe"
    plugin_paths = {
        "PythonScriptPlugin": engine_root / "Engine/Plugins/Experimental/PythonScriptPlugin/PythonScriptPlugin.uplugin",
        "EditorScriptingUtilities": engine_root / "Engine/Plugins/Editor/EditorScriptingUtilities/EditorScriptingUtilities.uplugin",
        "PCG": engine_root / "Engine/Plugins/Experimental/PCG/PCG.uplugin",
        "DataValidation": engine_root / "Engine/Plugins/Editor/DataValidation/DataValidation.uplugin",
        "MovieRenderPipeline": engine_root / "Engine/Plugins/MovieScene/MovieRenderPipeline/MovieRenderPipeline.uplugin",
        "WidgetEditorToolPalette": engine_root / "Engine/Plugins/Experimental/WidgetEditorToolPalette/WidgetEditorToolPalette.uplugin",
    }
    return {
        "project_dir": str(root),
        "uprojects": [str(path) for path in uprojects],
        "unreal_editor": str(editor),
        "unreal_editor_exists": editor.exists(),
        "unreal_editor_cmd": str(editor_cmd),
        "unreal_editor_cmd_exists": editor_cmd.exists(),
        "free_memory_gb": get_free_memory_gb(),
        "plugins_available": {name: path.exists() for name, path in plugin_paths.items()},
    }


def require_build_allowed(project_dir: Path | None = None) -> dict:
    policy = load_resource_policy(project_dir)
    decision = evaluate_resource_mode(policy)
    if not decision["allowed"]:
        raise RuntimeError(decision.get("reason", "WorldForge resource policy blocked the build."))
    return decision
