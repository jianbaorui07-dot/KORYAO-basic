"""Validate UE packages through Asset Registry, EditorAssetLibrary, and disk."""

from __future__ import annotations

from pathlib import Path


def object_path_for_package(package_path: str) -> str:
    name = package_path.rsplit("/", 1)[-1]
    return f"{package_path}.{name}"


def package_to_disk(project_dir: str | Path, package_path: str, asset_type: str | None = None) -> Path:
    root = Path(project_dir)
    relative = package_path.replace("/Game/", "", 1)
    suffix = ".umap" if asset_type == "Map" or "/Maps/" in package_path else ".uasset"
    return root / "Content" / f"{relative}{suffix}"


def validate_package(project_dir: str | Path, package_path: str, asset_type: str | None = None) -> dict:
    disk_path = package_to_disk(project_dir, package_path, asset_type)
    result = {
        "package_path": package_path,
        "object_path": object_path_for_package(package_path),
        "disk_path": str(disk_path),
        "disk_exists": disk_path.exists(),
        "editor_asset_exists": False,
        "asset_registry_found": False,
        "is_real_ue_asset": disk_path.exists() and disk_path.suffix.lower() in (".uasset", ".umap"),
    }
    try:
        import unreal  # type: ignore

        result["editor_asset_exists"] = bool(unreal.EditorAssetLibrary.does_asset_exist(package_path))
        registry = unreal.AssetRegistryHelpers.get_asset_registry()
        asset_data = registry.get_asset_by_object_path(object_path_for_package(package_path))
        result["asset_registry_found"] = bool(asset_data and asset_data.is_valid())
    except Exception as exc:
        result["validation_error"] = str(exc)
    return result


def validate_packages(project_dir: str | Path, packages: list[dict]) -> list[dict]:
    return [validate_package(project_dir, item["package_path"], item.get("asset_type")) for item in packages]
