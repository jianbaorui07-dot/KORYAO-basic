"""Command-line construction helpers for visible UnrealEditor launches."""

from __future__ import annotations

from pathlib import Path
from typing import Any


DEFAULT_EDITOR = Path(r"<UE_5_2_ROOT>\Engine\Binaries\Win64\UnrealEditor.exe")


def quote(value: str | Path) -> str:
    text = str(value)
    if " " in text or "\\" in text or ":" in text:
        return f'"{text}"'
    return text


def preview_exec_cmd(script_path: Path) -> str:
    safe = str(script_path).replace("\\", "/")
    return f'py exec(open(r"{safe}").read())'


def build_preview_args(uproject: Path, map_asset_path: str, preview_script: Path) -> str:
    return f'{quote(uproject)} {map_asset_path} -nosplash -log -ExecCmds="{preview_exec_cmd(preview_script)}"'


def build_visible_editor_args(uproject: Path, map_asset_path: str) -> str:
    return f"{quote(uproject)} {map_asset_path} -log"


def launch_receipt_payload(recipe: dict[str, Any], editor_pid: int, args: str) -> dict[str, Any]:
    return {
        "scene_id": recipe.get("scene_id"),
        "map_asset_path": recipe.get("map_asset_path"),
        "editor_pid": editor_pid,
        "editor_args": args,
    }
