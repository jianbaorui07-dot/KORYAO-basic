"""Asset path registry for WF-0009."""

from __future__ import annotations

from pathlib import Path


SCENE_ROOT = "/Game/WorldForge/Scenes/WF0009_SnowTemple"
MAP = f"{SCENE_ROOT}/Maps/M_WF0009_SnowTemple_Playable"
BLUEPRINTS = [
    f"{SCENE_ROOT}/Blueprints/BP_WF0009_TempleAssembly",
    f"{SCENE_ROOT}/Blueprints/BP_WF0009_RobotScout",
    f"{SCENE_ROOT}/Blueprints/BP_WF0009_TempleTrigger",
    f"{SCENE_ROOT}/Blueprints/BP_WF0009_WeatherController",
    f"{SCENE_ROOT}/Blueprints/BP_WF0009_GameMode",
    f"{SCENE_ROOT}/Blueprints/BP_WF0009_PlayerPawn",
]
MATERIALS = [
    f"{SCENE_ROOT}/Materials/M_WF0009_SnowStone",
    f"{SCENE_ROOT}/Materials/M_WF0009_IceRock",
    f"{SCENE_ROOT}/Materials/M_WF0009_AncientDarkWood",
    f"{SCENE_ROOT}/Materials/M_WF0009_WeatheredBronze",
    f"{SCENE_ROOT}/Materials/M_WF0009_RobotCeramic",
]
MATERIAL_INSTANCES = [
    f"{SCENE_ROOT}/MaterialInstances/MI_WF0009_SnowStone_Cold",
    f"{SCENE_ROOT}/MaterialInstances/MI_WF0009_RobotWhite",
]
SEQUENCES = [
    f"{SCENE_ROOT}/Sequences/LS_WF0009_HeroShot",
]
REQUIRED_PACKAGES = [MAP] + BLUEPRINTS + MATERIALS + MATERIAL_INSTANCES + SEQUENCES


def package_to_content_file(project_dir: Path, package_path: str) -> Path:
    if not package_path.startswith("/Game/"):
        raise ValueError(f"Only /Game packages are supported: {package_path}")
    relative = package_path.removeprefix("/Game/")
    suffix = ".umap" if "/Maps/" in package_path else ".uasset"
    return project_dir / "Content" / f"{relative}{suffix}"


def filesystem_asset_status(project_dir: Path) -> dict:
    return {
        package: {
            "file": str(package_to_content_file(project_dir, package)),
            "exists": package_to_content_file(project_dir, package).exists(),
        }
        for package in REQUIRED_PACKAGES
    }


def unreal_asset_status() -> dict:
    try:
        import unreal  # type: ignore
    except Exception:
        return {package: {"exists": False, "reason": "unreal module unavailable"} for package in REQUIRED_PACKAGES}
    return {package: {"exists": unreal.EditorAssetLibrary.does_asset_exist(package)} for package in REQUIRED_PACKAGES}
