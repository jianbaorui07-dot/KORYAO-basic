"""Package save helpers that report failures explicitly."""

from __future__ import annotations


def save_loaded_asset(asset) -> dict:
    try:
        import unreal  # type: ignore

        ok = bool(unreal.EditorAssetLibrary.save_loaded_asset(asset))
        return {"saved": ok, "asset": str(asset.get_path_name()) if asset else None}
    except Exception as exc:
        return {"saved": False, "error": str(exc)}


def save_directory(package_dir: str) -> dict:
    try:
        import unreal  # type: ignore

        ok = bool(unreal.EditorAssetLibrary.save_directory(package_dir, only_if_is_dirty=False, recursive=True))
        return {"saved": ok, "directory": package_dir}
    except Exception as exc:
        return {"saved": False, "directory": package_dir, "error": str(exc)}
