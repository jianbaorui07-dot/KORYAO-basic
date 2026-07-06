"""Preview helpers for WorldForge."""

from __future__ import annotations

from pathlib import Path


def preview_path(project_dir: Path) -> Path:
    return project_dir / "Saved" / "WorldForge" / "Previews" / "WF0009_v0.9-real_editor_preview.png"


def take_editor_preview(project_dir: Path) -> dict:
    try:
        import unreal  # type: ignore
    except Exception as exc:
        return {"created": False, "reason": f"unreal module unavailable: {exc}"}
    out_path = preview_path(project_dir)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        unreal.AutomationLibrary.take_high_res_screenshot(1280, 720, str(out_path))
    except Exception as exc:
        return {"created": False, "path": str(out_path), "reason": str(exc)}
    return {"created": True, "path": str(out_path), "type": "unreal_editor_screenshot"}
