"""Snapshot inspection and guarded restore helpers."""

from __future__ import annotations

import os
import shutil
from pathlib import Path


def list_snapshots(project_dir: Path) -> list[str]:
    root = project_dir / "Saved" / "WorldForge" / "Snapshots"
    if not root.exists():
        return []
    return [str(path) for path in sorted(root.iterdir()) if path.is_dir()]


def restore_snapshot(project_dir: Path, snapshot_dir: str | Path) -> dict:
    if os.environ.get("WORLDFORGE_ALLOW_RESTORE") != "1":
        return {
            "restored": False,
            "reason": "Restore is guarded. Set WORLDFORGE_ALLOW_RESTORE=1 only after explicit user approval.",
        }
    snapshot = Path(snapshot_dir)
    if not snapshot.exists():
        return {"restored": False, "reason": f"snapshot not found: {snapshot}"}
    restored = []
    mapping = {
        "我的项目8.uproject": project_dir / "我的项目8.uproject",
        "Config_DefaultEngine.ini": project_dir / "Config" / "DefaultEngine.ini",
        "WorldForgeEditorScripts_WF0009_create_mountain_temple_scene_editor_only.py": project_dir
        / "WorldForgeEditorScripts"
        / "WF0009_create_mountain_temple_scene_editor_only.py",
    }
    for backup_name, target in mapping.items():
        src = snapshot / backup_name
        if src.exists():
            shutil.copy2(src, target)
            restored.append(str(target))
    return {"restored": bool(restored), "targets": restored}
