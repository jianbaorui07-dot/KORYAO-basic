"""Scene-independent build orchestration decisions."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def map_disk_path(project_root: Path, map_asset_path: str) -> Path:
    if not map_asset_path.startswith("/Game/"):
        raise ValueError(f"Unsupported map asset path: {map_asset_path}")
    relative = map_asset_path[len("/Game/") :] + ".umap"
    return project_root / "Content" / Path(relative.replace("/", "\\"))


def build_decision(recipe: dict[str, Any], project_root: Path) -> dict[str, Any]:
    strategy = recipe.get("build_strategy", "recipe_builder")
    disk_path = map_disk_path(project_root, recipe["map_asset_path"])
    if strategy == "existing_validated_map" and disk_path.exists():
        return {
            "action": "skip_build",
            "reason": "existing_validated_map",
            "map_disk_path": str(disk_path),
        }
    if recipe.get("mode") == "DEFINITION_ONLY":
        return {
            "action": "skip_build",
            "reason": "definition_only_recipe",
            "map_disk_path": str(disk_path),
        }
    return {
        "action": "build_required",
        "reason": strategy,
        "map_disk_path": str(disk_path),
    }


def assert_no_wf0009_rebuild(recipe: dict[str, Any]) -> None:
    if recipe.get("scene_id") == "WF0009" and recipe.get("build_strategy") != "existing_validated_map":
        raise RuntimeError("WF0009 golden sample must not be rebuilt by the generic runner.")
