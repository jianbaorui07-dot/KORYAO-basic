"""Small map helpers for UE editor builds."""

from __future__ import annotations


def create_or_open_level(package_path: str) -> dict:
    try:
        import unreal  # type: ignore

        if unreal.EditorAssetLibrary.does_asset_exist(package_path):
            unreal.EditorLevelLibrary.load_level(package_path)
            action = "loaded"
        else:
            unreal.EditorLevelLibrary.new_level(package_path)
            action = "created"
        saved = bool(unreal.EditorLevelLibrary.save_current_level())
        return {"ok": saved, "action": action, "package_path": package_path}
    except Exception as exc:
        return {"ok": False, "package_path": package_path, "error": str(exc)}
