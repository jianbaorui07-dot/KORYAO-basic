"""WF0010 minimal recipe adapter.

Runs inside UnrealEditor-Cmd. It builds only lightweight primitive geometry for
the WF0010 recipe and is idempotent against actors tagged WF0010+WF_GENERATED.
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any


def _bootstrap() -> Path:
    script_path = Path(__file__).resolve()
    python_root = script_path.parents[2]
    if str(python_root) not in sys.path:
        sys.path.insert(0, str(python_root))
    return script_path.parents[4]


PROJECT_ROOT = Path(os.environ.get("WORLDFORGE_PROJECT_ROOT") or _bootstrap()).resolve()

from worldforge.Core import recipe_path_resolver, scene_validator, state_manager  # noqa: E402

import unreal  # type: ignore  # noqa: E402


RECIPE_PATH = recipe_path_resolver.resolve(
    os.environ.get("WORLDFORGE_RECIPE_PATH") or Path(__file__).with_suffix(".json"),
    PROJECT_ROOT,
)
RECIPE = scene_validator.load_recipe(RECIPE_PATH)
SCENE_ID = RECIPE["scene_id"]
REVISION = RECIPE.get("scene_revision", "R1")
MAP_PATH = RECIPE["map_asset_path"]
SCENE_ROOT = "/Game/WorldForge/Scenes/WF0010_DNABonsaiWorkshop"
TAGS = RECIPE.get("constraints", {}).get("required_tags", ["WF0010", "WF_GENERATED", "R1_LIGHTWEIGHT"])
RECEIPT_PATH = PROJECT_ROOT / "Saved" / "WorldForge" / "Receipts" / "WF0010_R1_closed_loop_receipt.json"
WARNINGS: list[str] = []


def now_iso() -> str:
    return datetime.now().astimezone().isoformat()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_dirs() -> None:
    for path in [f"{SCENE_ROOT}/Maps", f"{SCENE_ROOT}/Materials"]:
        if not unreal.EditorAssetLibrary.does_directory_exist(path):
            unreal.EditorAssetLibrary.make_directory(path)


def make_material(asset_path: str, color: tuple[float, float, float, float], metallic: float = 0.0, roughness: float = 0.72):
    directory, name = asset_path.rsplit("/", 1)
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        return unreal.EditorAssetLibrary.load_asset(asset_path)
    if not unreal.EditorAssetLibrary.does_directory_exist(directory):
        unreal.EditorAssetLibrary.make_directory(directory)
    factory = unreal.MaterialFactoryNew()
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, directory, unreal.Material, factory)
    try:
        opacity = color[3]
        if opacity < 0.99:
            material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
            material.set_editor_property("two_sided", True)
        base = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionConstant3Vector, -500, -80
        )
        base.set_editor_property("constant", unreal.LinearColor(color[0], color[1], color[2], 1.0))
        unreal.MaterialEditingLibrary.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
        rough = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionConstant, -500, 120
        )
        rough.set_editor_property("r", roughness)
        unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
        metal = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionConstant, -500, 220
        )
        metal.set_editor_property("r", metallic)
        unreal.MaterialEditingLibrary.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
        if opacity < 0.99:
            alpha = unreal.MaterialEditingLibrary.create_material_expression(
                material, unreal.MaterialExpressionConstant, -500, 20
            )
            alpha.set_editor_property("r", opacity)
            unreal.MaterialEditingLibrary.connect_material_property(alpha, "", unreal.MaterialProperty.MP_OPACITY)
        unreal.MaterialEditingLibrary.recompile_material(material)
    except Exception as exc:
        WARNINGS.append(f"material_color_setup_failed:{asset_path}:{exc}")
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def build_materials() -> dict[str, Any]:
    root = f"{SCENE_ROOT}/Materials"
    return {
        "wall": make_material(f"{root}/M_WF0010_Mineral_OffWhite", (0.82, 0.79, 0.70, 1.0), 0.0, 0.85),
        "stone": make_material(f"{root}/M_WF0010_LightGray_Stone", (0.46, 0.48, 0.48, 1.0), 0.0, 0.78),
        "pot": make_material(f"{root}/M_WF0010_Dark_Matte_Pot", (0.025, 0.020, 0.018, 1.0), 0.0, 0.92),
        "titanium": make_material(f"{root}/M_WF0010_Titanium_Silver", (0.67, 0.70, 0.70, 1.0), 0.55, 0.32),
        "gunmetal": make_material(f"{root}/M_WF0010_Gunmetal_BlackIron", (0.06, 0.065, 0.07, 1.0), 0.45, 0.45),
        "glass": make_material(f"{root}/M_WF0010_Clear_Glass", (0.72, 0.90, 1.0, 0.36), 0.0, 0.05),
        "red": make_material(f"{root}/M_WF0010_Node_DeepRed", (0.42, 0.02, 0.035, 1.0), 0.0, 0.55),
        "blue": make_material(f"{root}/M_WF0010_Node_CobaltBlue", (0.02, 0.12, 0.58, 1.0), 0.0, 0.5),
        "black": make_material(f"{root}/M_WF0010_Node_MatteBlack", (0.0, 0.0, 0.0, 1.0), 0.0, 0.94),
        "milk": make_material(f"{root}/M_WF0010_Node_MilkWhite", (0.92, 0.90, 0.84, 1.0), 0.0, 0.64),
    }


def actor_tags(actor: Any) -> set[str]:
    return {str(tag) for tag in actor.tags}


def ue_rotator(pitch: float, yaw: float, roll: float = 0.0):
    # UE 5.2 Python Rotator positional args are roll, pitch, yaw.
    return unreal.Rotator(roll, pitch, yaw)


def is_generated(actor: Any) -> bool:
    tags = actor_tags(actor)
    return "WF0010" in tags and "WF_GENERATED" in tags


def find_actor(label: str):
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    return None


def set_common(actor: Any, label: str, loc: tuple[float, float, float], rot: tuple[float, float, float], scale: tuple[float, float, float]) -> None:
    actor.set_actor_label(label)
    actor.tags = TAGS
    actor.set_actor_location(unreal.Vector(*loc), False, False)
    actor.set_actor_rotation(ue_rotator(*rot), False)
    actor.set_actor_scale3d(unreal.Vector(*scale))


def static_component(actor: Any):
    return actor.get_component_by_class(unreal.StaticMeshComponent)


def ensure_mesh(
    label: str,
    primitive: str,
    loc: tuple[float, float, float],
    rot: tuple[float, float, float],
    scale: tuple[float, float, float],
    material: Any,
):
    existing = find_actor(label)
    if existing is not None and not is_generated(existing):
        raise RuntimeError(f"Existing non-generated actor blocks WF0010 label: {label}")
    if existing is not None and existing.get_class().get_name() != "StaticMeshActor":
        unreal.EditorLevelLibrary.destroy_actor(existing)
        existing = None
    if existing is None:
        mesh = unreal.EditorAssetLibrary.load_asset(f"/Engine/BasicShapes/{primitive}.{primitive}")
        if mesh is None:
            raise RuntimeError(f"Missing engine primitive: {primitive}")
        existing = unreal.EditorLevelLibrary.spawn_actor_from_object(mesh, unreal.Vector(*loc), ue_rotator(*rot))
    set_common(existing, label, loc, rot, scale)
    comp = static_component(existing)
    if comp is not None and material is not None:
        comp.set_material(0, material)
    return existing


def ensure_actor_class(label: str, cls: Any, loc: tuple[float, float, float], rot: tuple[float, float, float]):
    existing = find_actor(label)
    if existing is not None and not is_generated(existing):
        raise RuntimeError(f"Existing non-generated actor blocks WF0010 label: {label}")
    if existing is not None and existing.get_class().get_name() != cls.static_class().get_name():
        unreal.EditorLevelLibrary.destroy_actor(existing)
        existing = None
    if existing is None:
        existing = unreal.EditorLevelLibrary.spawn_actor_from_class(cls, unreal.Vector(*loc), ue_rotator(*rot))
    set_common(existing, label, loc, rot, (1.0, 1.0, 1.0))
    return existing


def actor_component(actor: Any, cls: Any):
    try:
        return actor.get_component_by_class(cls)
    except Exception:
        return None


def clean_generated(expected_labels: set[str]) -> None:
    for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        if is_generated(actor) and actor.get_actor_label() not in expected_labels:
            unreal.EditorLevelLibrary.destroy_actor(actor)


def build_scene() -> dict[str, Any]:
    ensure_dirs()
    if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        unreal.EditorLevelLibrary.load_level(MAP_PATH)
    else:
        unreal.EditorLevelLibrary.new_level(MAP_PATH)
    expected_labels = {item["label"] for item in RECIPE["required_elements"]}
    clean_generated(expected_labels)
    materials = build_materials()

    ensure_mesh("WF0010_R1_Mineral_Floor", "Cube", (0, 0, -28), (0, 0, 0), (12.0, 8.5, 0.18), materials["wall"])
    ensure_mesh("WF0010_R1_Mineral_BackgroundWall", "Cube", (310, 0, 225), (0, 0, 0), (0.18, 8.5, 5.6), materials["wall"])
    ensure_mesh("WF0010_R1_Stone_Workbench", "Cube", (-55, 0, 35), (0, 0, 0), (5.6, 2.75, 0.36), materials["stone"])
    ensure_mesh("WF0010_R1_Matte_Rectangular_Pot_Base", "Cube", (-70, 0, 88), (0, 0, 0), (2.25, 1.05, 0.26), materials["pot"])
    ensure_mesh("WF0010_R1_Matte_Rectangular_Pot_FrontRim", "Cube", (-70, -62, 112), (0, 0, 0), (2.32, 0.12, 0.34), materials["pot"])
    ensure_mesh("WF0010_R1_Matte_Rectangular_Pot_BackRim", "Cube", (-70, 62, 112), (0, 0, 0), (2.32, 0.12, 0.34), materials["pot"])
    ensure_mesh("WF0010_R1_Matte_Rectangular_Pot_LeftRim", "Cube", (-190, 0, 112), (0, 0, 0), (0.13, 1.05, 0.34), materials["pot"])
    ensure_mesh("WF0010_R1_Matte_Rectangular_Pot_RightRim", "Cube", (50, 0, 112), (0, 0, 0), (0.13, 1.05, 0.34), materials["pot"])

    ensure_mesh("WF0010_R1_DNA_Trunk_LeftHelix", "Cylinder", (-105, -22, 210), (0, -8, 0), (0.12, 0.12, 1.95), materials["titanium"])
    ensure_mesh("WF0010_R1_DNA_Trunk_RightHelix", "Cylinder", (-35, 22, 210), (0, 8, 0), (0.12, 0.12, 1.95), materials["glass"])
    ensure_mesh("WF0010_R1_DNA_Rung_01", "Cylinder", (-70, 0, 160), (0, 84, 0), (0.055, 0.055, 0.78), materials["gunmetal"])
    ensure_mesh("WF0010_R1_DNA_Rung_02", "Cylinder", (-70, 0, 220), (0, 96, 0), (0.055, 0.055, 0.78), materials["gunmetal"])
    ensure_mesh("WF0010_R1_DNA_Rung_03", "Cylinder", (-70, 0, 280), (0, 74, 0), (0.055, 0.055, 0.78), materials["gunmetal"])
    ensure_mesh("WF0010_R1_DNA_Branch_Left", "Cylinder", (-137, -62, 290), (-38, 28, -18), (0.07, 0.07, 1.0), materials["glass"])
    ensure_mesh("WF0010_R1_DNA_Branch_Right", "Cylinder", (-12, 66, 303), (-34, -34, 20), (0.07, 0.07, 1.05), materials["titanium"])

    ensure_mesh("WF0010_R1_Molecular_Node_DeepRed", "Sphere", (-146, -92, 337), (0, 0, 0), (0.34, 0.34, 0.34), materials["red"])
    ensure_mesh("WF0010_R1_Molecular_Node_CobaltBlue", "Sphere", (9, 100, 350), (0, 0, 0), (0.32, 0.32, 0.32), materials["blue"])
    ensure_mesh("WF0010_R1_Molecular_Node_MatteBlack", "Sphere", (-112, 44, 252), (0, 0, 0), (0.26, 0.26, 0.26), materials["black"])
    ensure_mesh("WF0010_R1_Molecular_Node_MilkWhite", "Sphere", (-32, -42, 192), (0, 0, 0), (0.28, 0.28, 0.28), materials["milk"])
    ensure_mesh("WF0010_R1_Transparent_BranchTip_Left", "Sphere", (-198, -132, 371), (0, 0, 0), (0.22, 0.22, 0.22), materials["glass"])
    ensure_mesh("WF0010_R1_Transparent_BranchTip_Right", "Sphere", (58, 143, 384), (0, 0, 0), (0.22, 0.22, 0.22), materials["glass"])

    sun = ensure_actor_class("WF0010_R1_DirectionalLight", unreal.DirectionalLight, (-380, -420, 540), (-35, -42, 0))
    sun_comp = actor_component(sun, unreal.DirectionalLightComponent)
    if sun_comp is not None:
        sun_comp.set_editor_property("intensity", 2.4)
    else:
        WARNINGS.append("directional_light_component_not_found")
    sky = ensure_actor_class("WF0010_R1_SkyLight", unreal.SkyLight, (0, 0, 360), (0, 0, 0))
    sky_comp = actor_component(sky, unreal.SkyLightComponent)
    if sky_comp is not None:
        sky_comp.set_editor_property("intensity", 0.45)
    else:
        WARNINGS.append("sky_light_component_not_found")
    fog = ensure_actor_class("WF0010_R1_ExponentialHeightFog", unreal.ExponentialHeightFog, (0, 0, 0), (0, 0, 0))
    fog_comp = actor_component(fog, unreal.ExponentialHeightFogComponent)
    if fog_comp is not None:
        fog_comp.set_editor_property("fog_density", 0.012)
        fog_comp.set_editor_property("fog_height_falloff", 0.22)
    camera = ensure_actor_class("WF0010_R1_CineCameraActor", unreal.CineCameraActor, (-520, -410, 265), (-10, 42, 0))
    try:
        cine = camera.get_cine_camera_component()
        cine.set_editor_property("current_focal_length", 35.0)
    except Exception as exc:
        WARNINGS.append(f"camera_focal_length_warning:{exc}")

    unreal.EditorLevelLibrary.save_current_level()
    unreal.EditorAssetLibrary.save_directory(SCENE_ROOT, only_if_is_dirty=False, recursive=True)
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    generated = [actor.get_actor_label() for actor in actors if is_generated(actor)]
    validation = scene_validator.validate_scene_in_editor(RECIPE, PROJECT_ROOT)
    return {
        "map_asset_path": MAP_PATH,
        "map_disk_path": str(scene_validator.map_disk_path(PROJECT_ROOT, MAP_PATH)),
        "actor_count": len(actors),
        "generated_actor_count": len(generated),
        "generated_labels": sorted(generated),
        "validation": validation,
        "warnings": WARNINGS,
    }


def main() -> None:
    receipt: dict[str, Any] = {
        "scene_id": SCENE_ID,
        "scene_revision": REVISION,
        "recipe_path": str(RECIPE_PATH),
        "map_asset_path": MAP_PATH,
        "started_at": now_iso(),
        "status": "running",
    }
    write_json(RECEIPT_PATH, receipt)
    state_manager.write_state(
        {
            "phase": "BUILD_RUNNING",
            "job_phase": "BUILD_RUNNING",
            "framework_version": state_manager.FRAMEWORK_VERSION,
            "active_scene_id": SCENE_ID,
            "active_recipe_path": str(RECIPE_PATH),
            "requested_map_path": MAP_PATH,
            "last_receipt_path": str(RECEIPT_PATH),
            "last_error": "",
        },
        PROJECT_ROOT,
    )
    try:
        result = build_scene()
        ok = bool(result["validation"].get("ok")) and 18 <= int(result["actor_count"]) <= 30
        receipt.update(result)
        receipt["status"] = "build_ready" if ok else "validation_failed"
        receipt["finished_at"] = now_iso()
        write_json(RECEIPT_PATH, receipt)
        state_manager.write_state(
            {
                "phase": "BUILD_READY" if ok else "FAILED",
                "job_phase": "BUILD_READY" if ok else "FAILED",
                "actual_map_exists": Path(result["map_disk_path"]).exists(),
                "actual_actor_count": result["actor_count"],
                "validation_receipt_path": str(RECEIPT_PATH),
                "last_receipt_path": str(RECEIPT_PATH),
                "last_error": "" if ok else "WF0010_validation_failed_after_build",
            },
            PROJECT_ROOT,
        )
        if not ok:
            raise RuntimeError("WF0010 validation failed after build")
    except Exception as exc:
        receipt["status"] = "failed"
        receipt["error"] = str(exc)
        receipt["traceback"] = traceback.format_exc()
        receipt["finished_at"] = now_iso()
        write_json(RECEIPT_PATH, receipt)
        state_manager.write_state(
            {"phase": "FAILED", "job_phase": "FAILED", "last_error": str(exc), "last_receipt_path": str(RECEIPT_PATH)},
            PROJECT_ROOT,
        )
        raise


main()
