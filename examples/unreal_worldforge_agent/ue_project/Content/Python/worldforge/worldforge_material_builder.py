"""Material creation helpers for WorldForge editor builds."""

from __future__ import annotations

from . import worldforge_asset_registry as registry


def _unreal():
    import unreal  # type: ignore

    return unreal


def ensure_directory(path: str) -> None:
    unreal = _unreal()
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def create_material(package_path: str):
    unreal = _unreal()
    directory, name = package_path.rsplit("/", 1)
    ensure_directory(directory)
    if unreal.EditorAssetLibrary.does_asset_exist(package_path):
        return unreal.load_asset(package_path)
    factory = unreal.MaterialFactoryNew()
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, directory, unreal.Material, factory)
    asset.set_editor_property("two_sided", False)
    unreal.EditorAssetLibrary.save_loaded_asset(asset)
    return asset


def create_material_instance(package_path: str, parent_package_path: str):
    unreal = _unreal()
    directory, name = package_path.rsplit("/", 1)
    ensure_directory(directory)
    if unreal.EditorAssetLibrary.does_asset_exist(package_path):
        return unreal.load_asset(package_path)
    parent = unreal.load_asset(parent_package_path)
    factory = unreal.MaterialInstanceConstantFactoryNew()
    try:
        factory.set_editor_property("initial_parent", parent)
    except Exception:
        pass
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name,
        directory,
        unreal.MaterialInstanceConstant,
        factory,
    )
    try:
        asset.set_editor_property("parent", parent)
    except Exception:
        pass
    unreal.EditorAssetLibrary.save_loaded_asset(asset)
    return asset


def build_wf0009_materials() -> dict:
    created = {}
    for package in registry.MATERIALS:
        created[package] = create_material(package)
    created[registry.MATERIAL_INSTANCES[0]] = create_material_instance(
        registry.MATERIAL_INSTANCES[0],
        f"{registry.SCENE_ROOT}/Materials/M_WF0009_SnowStone",
    )
    created[registry.MATERIAL_INSTANCES[1]] = create_material_instance(
        registry.MATERIAL_INSTANCES[1],
        f"{registry.SCENE_ROOT}/Materials/M_WF0009_RobotCeramic",
    )
    return created
