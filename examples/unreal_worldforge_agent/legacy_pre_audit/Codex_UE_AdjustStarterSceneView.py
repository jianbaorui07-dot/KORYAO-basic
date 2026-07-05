# ruff: noqa
# fmt: off
import json
import os
import traceback

import unreal


MAP_PATH = "/Game/CodexTests/Codex_StarterScene"
OUTPUT_DIR = r"<WORLDFORGE_ROOT>"
RESULT_PATH = os.path.join(OUTPUT_DIR, "Codex_UE_AdjustStarterSceneView_result.json")


def write_result(data):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(RESULT_PATH, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def find_actor(label):
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    raise RuntimeError(f"Actor not found: {label}")


def main():
    if not unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        raise RuntimeError(f"Target map missing: {MAP_PATH}")

    world = unreal.EditorLevelLibrary.get_editor_world()
    if not world or world.get_path_name() != MAP_PATH + "." + MAP_PATH.rsplit("/", 1)[-1]:
        if not unreal.EditorLevelLibrary.load_level(MAP_PATH):
            raise RuntimeError(f"Failed to load target map: {MAP_PATH}")

    camera = find_actor("CODEX_TEST_Camera")
    light = find_actor("CODEX_TEST_Light")

    camera_location = unreal.Vector(0.0, 650.0, 300.0)
    camera_rotation = unreal.MathLibrary.find_look_at_rotation(camera_location, unreal.Vector(0.0, 0.0, 55.0))
    camera.set_actor_location(camera_location, False, True)
    camera.set_actor_rotation(camera_rotation, True)

    light.set_actor_location(unreal.Vector(160.0, 280.0, 420.0), False, True)

    unreal.EditorLevelLibrary.set_level_viewport_camera_info(camera_location, camera_rotation)
    unreal.EditorLevelLibrary.editor_invalidate_viewports()

    if not unreal.EditorLevelLibrary.save_current_level():
        raise RuntimeError(f"Failed to save current level: {MAP_PATH}")

    write_result(
        {
            "success": True,
            "map_path": MAP_PATH,
            "adjusted": ["CODEX_TEST_Camera", "CODEX_TEST_Light"],
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
