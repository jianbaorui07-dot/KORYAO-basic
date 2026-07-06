"""Blueprint asset creation helpers for WorldForge editor builds."""

from __future__ import annotations

from . import worldforge_asset_registry as registry


def _unreal():
    import unreal  # type: ignore

    return unreal


def ensure_directory(path: str) -> None:
    unreal = _unreal()
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def create_blueprint(package_path: str, parent_class):
    unreal = _unreal()
    directory, name = package_path.rsplit("/", 1)
    ensure_directory(directory)
    if unreal.EditorAssetLibrary.does_asset_exist(package_path):
        return unreal.load_asset(package_path)
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", parent_class)
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, directory, unreal.Blueprint, factory)
    unreal.EditorAssetLibrary.save_loaded_asset(asset)
    return asset


def build_wf0009_blueprints() -> dict:
    unreal = _unreal()
    parents = {
        "BP_WF0009_TempleAssembly": unreal.Actor,
        "BP_WF0009_RobotScout": unreal.Actor,
        "BP_WF0009_TempleTrigger": unreal.Actor,
        "BP_WF0009_WeatherController": unreal.Actor,
        "BP_WF0009_GameMode": unreal.GameModeBase,
        "BP_WF0009_PlayerPawn": unreal.DefaultPawn,
    }
    created = {}
    for package in registry.BLUEPRINTS:
        name = package.rsplit("/", 1)[1]
        created[package] = create_blueprint(package, parents[name])
    return created
