# ruff: noqa
# fmt: off
import json
import os
import traceback

import unreal


MAP_DIR = "/Game/CodexTests"
MAP_NAME = "Codex_StarterScene"
MAP_PATH = f"{MAP_DIR}/{MAP_NAME}"
OUTPUT_DIR = r"<WORLDFORGE_ROOT>"
RESULT_PATH = os.path.join(OUTPUT_DIR, "Codex_UE_CreateStarterScene_result.json")


def write_result(data):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(RESULT_PATH, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def require_asset(path):
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if not asset:
        raise RuntimeError(f"Required engine asset not found: {path}")
    return asset


def set_label(actor, label):
    actor.set_actor_label(label, mark_dirty=True)
    return actor


def static_mesh_actor(label, mesh_path, location, scale):
    mesh = require_asset(mesh_path)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(*location),
        unreal.Rotator(0.0, 0.0, 0.0),
    )
    if not actor:
        raise RuntimeError(f"Failed to spawn {label}")
    set_label(actor, label)
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if not component:
        raise RuntimeError(f"StaticMeshComponent missing for {label}")
    component.set_static_mesh(mesh)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    return actor


def main():
    if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        raise RuntimeError(f"Target map already exists; refusing to overwrite: {MAP_PATH}")

    unreal.EditorAssetLibrary.make_directory(MAP_DIR)

    if not unreal.EditorLevelLibrary.new_level(MAP_PATH):
        raise RuntimeError(f"Failed to create new level: {MAP_PATH}")

    created = []
    floor = static_mesh_actor(
        "CODEX_TEST_Floor",
        "/Engine/BasicShapes/Plane.Plane",
        (0.0, 0.0, 0.0),
        (8.0, 8.0, 1.0),
    )
    created.append(floor.get_actor_label())

    cube = static_mesh_actor(
        "CODEX_TEST_Cube_Left",
        "/Engine/BasicShapes/Cube.Cube",
        (-220.0, 0.0, 50.0),
        (1.0, 1.0, 1.0),
    )
    created.append(cube.get_actor_label())

    sphere = static_mesh_actor(
        "CODEX_TEST_Sphere_Center",
        "/Engine/BasicShapes/Sphere.Sphere",
        (0.0, 0.0, 50.0),
        (1.0, 1.0, 1.0),
    )
    created.append(sphere.get_actor_label())

    cylinder = static_mesh_actor(
        "CODEX_TEST_Cylinder_Right",
        "/Engine/BasicShapes/Cylinder.Cylinder",
        (220.0, 0.0, 50.0),
        (1.0, 1.0, 1.0),
    )
    created.append(cylinder.get_actor_label())

    light = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.PointLight,
        unreal.Vector(-120.0, -260.0, 420.0),
        unreal.Rotator(-45.0, 35.0, 0.0),
    )
    if not light:
        raise RuntimeError("Failed to spawn CODEX_TEST_Light")
    set_label(light, "CODEX_TEST_Light")
    light_component = light.get_component_by_class(unreal.PointLightComponent)
    if light_component:
        light_component.set_intensity(4500.0)
        light_component.set_attenuation_radius(900.0)
    created.append(light.get_actor_label())

    camera_location = unreal.Vector(0.0, -650.0, 300.0)
    camera_rotation = unreal.MathLibrary.find_look_at_rotation(camera_location, unreal.Vector(0.0, 0.0, 55.0))
    camera = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.CameraActor,
        camera_location,
        camera_rotation,
    )
    if not camera:
        raise RuntimeError("Failed to spawn CODEX_TEST_Camera")
    set_label(camera, "CODEX_TEST_Camera")
    created.append(camera.get_actor_label())

    unreal.EditorLevelLibrary.set_level_viewport_camera_info(camera_location, camera_rotation)
    unreal.EditorLevelLibrary.editor_invalidate_viewports()

    if not unreal.EditorLevelLibrary.save_current_level():
        raise RuntimeError(f"Failed to save current level: {MAP_PATH}")

    write_result(
        {
            "success": True,
            "map_path": MAP_PATH,
            "actors": created,
            "result_path": RESULT_PATH,
        }
    )


try:
    main()
except Exception as exc:
    write_result(
        {
            "success": False,
            "error": str(exc),
            "traceback": traceback.format_exc(),
            "map_path": MAP_PATH,
            "result_path": RESULT_PATH,
        }
    )
    raise
