"""Commandlet probe that creates minimal assets only under /Game/WorldForge/_Probe/."""

from __future__ import annotations

import json
import time
from pathlib import Path

from .execution_logger import ExecutionLogger
from . import memory_guard
from . import package_saver
from . import package_validator


PROBE_ROOT = "/Game/WorldForge/_Probe"


def _ensure_probe_dir(unreal) -> None:
    if not unreal.EditorAssetLibrary.does_directory_exist(PROBE_ROOT):
        unreal.EditorAssetLibrary.make_directory(PROBE_ROOT)


def _asset_name(job_id: str, kind: str) -> str:
    safe = "".join(ch if ch.isalnum() else "_" for ch in job_id)
    return f"WF_Probe_{kind}_{safe}"


def create_probe_assets(project_dir: str | Path, ledger_dir: str | Path, job_id: str) -> dict:
    import unreal  # type: ignore

    logger = ExecutionLogger(ledger_dir)
    started = time.time()
    logger.event("info", "commandlet_probe_start", job_id=job_id, probe_root=PROBE_ROOT)
    _ensure_probe_dir(unreal)
    packages: list[dict] = []
    created: list[dict] = []

    material_package = f"{PROBE_ROOT}/{_asset_name(job_id, 'Material')}"
    material_name = material_package.rsplit("/", 1)[-1]
    if not unreal.EditorAssetLibrary.does_asset_exist(material_package):
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            material_name,
            PROBE_ROOT,
            unreal.Material,
            unreal.MaterialFactoryNew(),
        )
    else:
        material = unreal.load_asset(material_package)
    saved = package_saver.save_loaded_asset(material)
    created.append({"kind": "Material", "package_path": material_package, "save": saved})
    packages.append({"asset_type": "Material", "package_path": material_package})
    logger.event("info", "material_probe_saved", package_path=material_package, save=saved)

    blueprint_package = f"{PROBE_ROOT}/{_asset_name(job_id, 'Blueprint')}"
    blueprint_name = blueprint_package.rsplit("/", 1)[-1]
    if not unreal.EditorAssetLibrary.does_asset_exist(blueprint_package):
        factory = unreal.BlueprintFactory()
        factory.set_editor_property("parent_class", unreal.Actor)
        blueprint = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            blueprint_name,
            PROBE_ROOT,
            unreal.Blueprint,
            factory,
        )
    else:
        blueprint = unreal.load_asset(blueprint_package)
    saved = package_saver.save_loaded_asset(blueprint)
    created.append({"kind": "Blueprint", "package_path": blueprint_package, "save": saved})
    packages.append({"asset_type": "Blueprint", "package_path": blueprint_package})
    logger.event("info", "blueprint_probe_saved", package_path=blueprint_package, save=saved)

    map_package = f"{PROBE_ROOT}/{_asset_name(job_id, 'Map')}"
    try:
        if not unreal.EditorAssetLibrary.does_asset_exist(map_package):
            unreal.EditorLevelLibrary.new_level(map_package)
            unreal.EditorLevelLibrary.save_current_level()
        else:
            unreal.EditorLevelLibrary.load_level(map_package)
            unreal.EditorLevelLibrary.save_current_level()
        map_error = None
    except Exception as exc:
        map_error = str(exc)
        logger.exception("map_probe_failed", exc)
    created.append({"kind": "Map", "package_path": map_package, "error": map_error})
    packages.append({"asset_type": "Map", "package_path": map_package})

    package_saver.save_directory(PROBE_ROOT)
    validation = package_validator.validate_packages(project_dir, packages)
    memory = memory_guard.snapshot()
    success = all(item.get("disk_exists") and item.get("editor_asset_exists") for item in validation)
    result = {
        "job_id": job_id,
        "status": "passed" if success else "failed",
        "probe_root": PROBE_ROOT,
        "duration_seconds": round(time.time() - started, 2),
        "created": created,
        "validation": validation,
        "memory": memory,
        "note": "Probe assets are intentionally retained when created successfully.",
    }
    out = Path(ledger_dir) / "commandlet_probe_result.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.event("info", "commandlet_probe_finish", status=result["status"], result=str(out))
    return result
