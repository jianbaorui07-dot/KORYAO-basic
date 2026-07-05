# ruff: noqa
# fmt: off
import json
import os
import time
import traceback

import unreal

RESULT = {
    "status": "started",
    "errors": [],
    "warnings": [],
    "created_assets": [],
    "created_actors": [],
    "actor_counts": {},
    "pie_smoke_test": "not_run",
}

TAG = "WorldForgeManaged"
STATE_VALUES = ["Idle", "Planning", "Preview", "Building", "Verifying", "Completed", "Failed", "Stopped"]
COMMAND_WHITELIST = [
    "BuildBasicLab",
    "PreviewFutureCityBlockout",
    "ExecuteFutureCityBlockout",
    "SetTestLightRotation",
    "CreateCheckpoint",
    "RestoreLastCheckpoint",
    "GetWorldSummary",
    "RunPIESmokeTest",
    "StopCurrentTask",
]


def project_dir():
    return os.path.normpath(unreal.Paths.project_dir())


def worldforge_root():
    return os.path.dirname(project_dir().rstrip("\\/"))


def out_path(*parts):
    return os.path.join(worldforge_root(), *parts)


def ensure_os_dir(path):
    os.makedirs(path, exist_ok=True)


def record_error(label, exc):
    RESULT["errors"].append({"label": label, "error": str(exc), "traceback": traceback.format_exc()})
    unreal.log_error("WorldForge error in %s: %s" % (label, exc))


def record_warning(msg):
    RESULT["warnings"].append(msg)
    unreal.log_warning("WorldForge warning: %s" % msg)


def asset_exists(package_path):
    try:
        return unreal.EditorAssetLibrary.does_asset_exist(package_path)
    except Exception:
        return False


def make_content_dirs():
    dirs = [
        "/Game/WorldForge",
        "/Game/WorldForge/Blueprints",
        "/Game/WorldForge/Maps",
        "/Game/WorldForge/Materials",
        "/Game/WorldForge/RemoteControl",
        "/Game/WorldForge/UI",
        "/Game/WorldForge/Data",
        "/Game/WorldForge/Checkpoints",
        "/Game/WorldForge/Tests",
        "/Game/WorldForge/Docs",
    ]
    for d in dirs:
        try:
            unreal.EditorAssetLibrary.make_directory(d)
        except Exception as exc:
            record_error("make_directory " + d, exc)


def asset_tools():
    return unreal.AssetToolsHelpers.get_asset_tools()


def save_asset(path):
    try:
        unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
    except Exception as exc:
        record_warning("save_asset failed for %s: %s" % (path, exc))


def create_material(name, color):
    package = "/Game/WorldForge/Materials"
    asset_path = package + "/" + name
    if asset_exists(asset_path):
        return unreal.EditorAssetLibrary.load_asset(asset_path)
    try:
        mat = asset_tools().create_asset(name, package, unreal.Material, unreal.MaterialFactoryNew())
        RESULT["created_assets"].append(asset_path)
        try:
            expr = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 0)
            expr.set_editor_property("constant", color)
            unreal.MaterialEditingLibrary.connect_material_property(expr, "", unreal.MaterialProperty.MP_BASE_COLOR)
            rough = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant, -350, 180)
            rough.set_editor_property("r", 0.82)
            unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
            unreal.MaterialEditingLibrary.recompile_material(mat)
        except Exception as exc:
            record_warning("material node setup fallback for %s: %s" % (name, exc))
        save_asset(asset_path)
        return mat
    except Exception as exc:
        record_error("create_material " + name, exc)
        return None


def create_blueprint(name, role_text):
    package = "/Game/WorldForge/Blueprints"
    asset_path = package + "/" + name
    if asset_exists(asset_path):
        return unreal.EditorAssetLibrary.load_asset(asset_path)
    try:
        factory = unreal.BlueprintFactory()
        try:
            factory.set_editor_property("parent_class", unreal.Actor)
        except Exception:
            pass
        bp = asset_tools().create_asset(name, package, unreal.Blueprint, factory)
        if bp:
            unreal.EditorAssetLibrary.set_metadata_tag(bp, "WorldForgeRole", role_text)
            unreal.EditorAssetLibrary.set_metadata_tag(bp, "WorldForgeAllowedStates", ",".join(STATE_VALUES))
            unreal.EditorAssetLibrary.set_metadata_tag(bp, "WorldForgeCommandWhitelist", ",".join(COMMAND_WHITELIST))
            RESULT["created_assets"].append(asset_path)
            save_asset(asset_path)
            return bp
    except Exception as exc:
        record_error("create_blueprint " + name, exc)
    return None


def create_widget_blueprint():
    package = "/Game/WorldForge/UI"
    name = "WBP_WorldForgeStatus"
    asset_path = package + "/" + name
    if asset_exists(asset_path):
        return unreal.EditorAssetLibrary.load_asset(asset_path)
    try:
        factory = unreal.WidgetBlueprintFactory()
        wb = asset_tools().create_asset(name, package, unreal.WidgetBlueprint, factory)
        if wb:
            unreal.EditorAssetLibrary.set_metadata_tag(wb, "WorldForgeRole", "Status display only: map, task, state, actor count, checkpoint, safety state")
            RESULT["created_assets"].append(asset_path)
            save_asset(asset_path)
            return wb
    except Exception as exc:
        record_error("create_widget_blueprint", exc)
    return None


def create_remote_control_preset():
    package = "/Game/WorldForge/RemoteControl"
    name = "RC_WorldForgeAgentFramework"
    asset_path = package + "/" + name
    if asset_exists(asset_path):
        return unreal.EditorAssetLibrary.load_asset(asset_path)
    try:
        cls = getattr(unreal, "RemoteControlPreset", None)
        factory_cls = getattr(unreal, "RemoteControlPresetFactory", None)
        if cls is None or factory_cls is None:
            record_warning("Remote Control preset classes unavailable; preset not created")
            return None
        preset = asset_tools().create_asset(name, package, cls, factory_cls())
        if preset:
            unreal.EditorAssetLibrary.set_metadata_tag(preset, "WorldForgeExposedTools", "HealthCheck,GetWorldSummary,PrintSmokeMessage,SetTestLightRotation,CreateCheckpoint,RestoreLastCheckpoint,PreviewApprovedPlan,ExecuteApprovedPlan,StopCurrentTask")
            RESULT["created_assets"].append(asset_path)
            save_asset(asset_path)
            return preset
    except Exception as exc:
        record_error("create_remote_control_preset", exc)
    return None


def tag_actor(actor):
    try:
        tags = list(actor.get_editor_property("tags"))
        if unreal.Name(TAG) not in tags:
            tags.append(unreal.Name(TAG))
            actor.set_editor_property("tags", tags)
    except Exception as exc:
        record_warning("could not tag actor %s: %s" % (actor.get_name(), exc))


def label_actor(actor, label):
    try:
        actor.set_actor_label(label)
    except Exception:
        pass


def set_mesh(actor, mesh, material=None):
    try:
        comp = actor.static_mesh_component
        comp.set_static_mesh(mesh)
        if material:
            comp.set_material(0, material)
    except Exception as exc:
        record_warning("set_mesh failed for %s: %s" % (actor.get_name(), exc))


def spawn(cls, label, loc, rot=None, scale=None, mesh=None, material=None):
    rot = rot or unreal.Rotator(0, 0, 0)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(cls, loc, rot)
    label_actor(actor, label)
    if scale is not None:
        actor.set_actor_scale3d(scale)
    if mesh is not None:
        set_mesh(actor, mesh, material)
    tag_actor(actor)
    RESULT["created_actors"].append(label)
    return actor


def set_light_intensity(actor, intensity):
    try:
        comp = actor.get_component_by_class(unreal.LightComponentBase)
        if comp:
            comp.set_editor_property("intensity", intensity)
    except Exception:
        try:
            actor.light_component.set_editor_property("intensity", intensity)
        except Exception:
            pass


def save_current_level(label):
    try:
        unreal.EditorLevelLibrary.save_current_level()
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
        RESULT["actor_counts"][label] = len(unreal.EditorLevelLibrary.get_all_level_actors())
    except Exception as exc:
        record_error("save_current_level " + label, exc)


def create_lab_map(materials):
    path = "/Game/WorldForge/Maps/M_WorldForgeLab"
    if asset_exists(path):
        record_warning("M_WorldForgeLab already exists; loading without overwrite")
        unreal.EditorLevelLibrary.load_level(path)
        return
    unreal.EditorLevelLibrary.new_level(path)
    cube_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")
    spawn(unreal.StaticMeshActor, "WORLDFORGE_LAB_Ground", unreal.Vector(0, 0, -10), scale=unreal.Vector(20, 20, 0.1), mesh=cube_mesh, material=materials.get("ground"))
    spawn(unreal.StaticMeshActor, "WORLDFORGE_LAB_TestCube", unreal.Vector(0, 0, 100), scale=unreal.Vector(1, 1, 1), mesh=cube_mesh, material=materials.get("accent"))
    sun = spawn(unreal.DirectionalLight, "WORLDFORGE_LAB_DirectionalLight", unreal.Vector(-300, -300, 500), unreal.Rotator(-35, -30, 0))
    set_light_intensity(sun, 2.0)
    spawn(unreal.SkyLight, "WORLDFORGE_LAB_SkyLight", unreal.Vector(0, 0, 250))
    spawn(unreal.PlayerStart, "WORLDFORGE_LAB_PlayerStart", unreal.Vector(-300, 0, 80))
    spawn(unreal.CameraActor, "WORLDFORGE_LAB_Camera", unreal.Vector(-650, -500, 360), unreal.Rotator(-25, 0, -38))
    try:
        txt = spawn(unreal.TextRenderActor, "WORLDFORGE_LAB_StatusText", unreal.Vector(-240, 0, 180), unreal.Rotator(0, 0, 0))
        txt.text_render.set_editor_property("text", "WORLDFORGE UE AGENT FRAMEWORK v0.1")
        txt.text_render.set_editor_property("world_size", 26.0)
    except Exception as exc:
        record_warning("status text unavailable: %s" % exc)
    save_current_level("M_WorldForgeLab")


def create_blockout_map(materials):
    path = "/Game/WorldForge/Maps/M_WorldForgeBlockoutSandbox"
    if asset_exists(path):
        record_warning("M_WorldForgeBlockoutSandbox already exists; loading without overwrite")
        unreal.EditorLevelLibrary.load_level(path)
        return
    unreal.EditorLevelLibrary.new_level(path)
    cube_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")
    spawn(unreal.StaticMeshActor, "WORLDFORGE_CITY_Ground", unreal.Vector(0, 0, -10), scale=unreal.Vector(60, 40, 0.1), mesh=cube_mesh, material=materials.get("ground"))
    spawn(unreal.StaticMeshActor, "WORLDFORGE_CITY_MainRoad", unreal.Vector(0, 0, 0), scale=unreal.Vector(4, 38, 0.04), mesh=cube_mesh, material=materials.get("road"))
    spawn(unreal.StaticMeshActor, "WORLDFORGE_CITY_Plaza", unreal.Vector(0, -650, 5), scale=unreal.Vector(12, 8, 0.05), mesh=cube_mesh, material=materials.get("plaza"))
    spawn(unreal.StaticMeshActor, "WORLDFORGE_CITY_CenterTower", unreal.Vector(0, 320, 420), scale=unreal.Vector(2.2, 2.2, 8.4), mesh=cube_mesh, material=materials.get("tower"))
    idx = 0
    for side, x in [("L", -520), ("R", 520)]:
        for row, y in enumerate([-900, -520, -120, 280, 700, 1060]):
            height = 1.8 + (row % 3) * 0.9
            idx += 1
            spawn(unreal.StaticMeshActor, "WORLDFORGE_CITY_Building_%s_%02d" % (side, idx), unreal.Vector(x, y, height * 50), scale=unreal.Vector(2.8, 2.1, height), mesh=cube_mesh, material=materials.get("building"))
    for y in [-1050, -750, -450, -150, 150, 450, 750, 1050]:
        light = spawn(unreal.PointLight, "WORLDFORGE_CITY_StreetLight_%s" % y, unreal.Vector(230, y, 130))
        set_light_intensity(light, 450.0)
    sun = spawn(unreal.DirectionalLight, "WORLDFORGE_CITY_MoonKeyLight", unreal.Vector(-700, -900, 900), unreal.Rotator(-18, -45, 0))
    set_light_intensity(sun, 0.35)
    sky = spawn(unreal.SkyLight, "WORLDFORGE_CITY_SkyLight", unreal.Vector(0, 0, 300))
    set_light_intensity(sky, 0.15)
    spawn(unreal.PlayerStart, "WORLDFORGE_CITY_PlayerStart", unreal.Vector(-250, -1050, 90))
    spawn(unreal.CameraActor, "WORLDFORGE_CITY_OverviewCamera", unreal.Vector(-1350, -1450, 950), unreal.Rotator(-35, 0, -42))
    save_current_level("M_WorldForgeBlockoutSandbox")


def write_text_plan():
    plan_dir = out_path("05_任务与检查点", "plans")
    ensure_os_dir(plan_dir)
    plan_path = os.path.join(plan_dir, "001_future_city_blockout_plan.md")
    text = """# 001 Future City Blockout Plan

- Center tower: world center line, north side, tall single placeholder cube.
- Road: one main north-south road through the map center.
- Building groups: six modular placeholder buildings on each side of the road.
- Plaza: small low plaza south of the tower, connected to road.
- Lighting: low-load moon key light, skylight, and eight point street lights.
- Estimated actor count: under 40, below limit 100.
- Performance risk: low; only basic cubes, built-in lights, no external assets, no Lumen, no Nanite, no path tracing.
"""
    with open(plan_path, "w", encoding="utf-8") as f:
        f.write(text)
    RESULT["created_assets"].append(plan_path)
    return plan_path


def write_checkpoint():
    cp_dir = out_path("05_任务与检查点", "checkpoints")
    ensure_os_dir(cp_dir)
    checkpoint = []
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            tags = [str(t) for t in actor.get_editor_property("tags")]
            if TAG not in tags:
                continue
            loc = actor.get_actor_location()
            rot = actor.get_actor_rotation()
            scale = actor.get_actor_scale3d()
            checkpoint.append({
                "label": actor.get_actor_label(),
                "class": actor.get_class().get_name(),
                "location": [loc.x, loc.y, loc.z],
                "rotation": [rot.roll, rot.pitch, rot.yaw],
                "scale": [scale.x, scale.y, scale.z],
            })
        except Exception as exc:
            record_warning("checkpoint actor skipped: %s" % exc)
    path = os.path.join(cp_dir, "checkpoint_001_future_city_initial.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"checkpoint_id": "001_initial", "actor_count": len(checkpoint), "actors": checkpoint}, f, ensure_ascii=False, indent=2)
    RESULT["checkpoint_path"] = path
    RESULT["checkpoint_actor_count"] = len(checkpoint)
    return path


def world_summary():
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    worldforge = []
    for actor in actors:
        try:
            if TAG in [str(t) for t in actor.get_editor_property("tags")]:
                worldforge.append(actor)
        except Exception:
            pass
    return {
        "map": str(unreal.EditorLevelLibrary.get_editor_world().get_name()),
        "total_actor_count": len(actors),
        "worldforge_actor_count": len(worldforge),
        "allowed_to_continue": len(worldforge) <= 100,
    }


def run_pie_smoke_test(seconds):
    try:
        if hasattr(unreal.EditorLevelLibrary, "editor_play_simulate") and hasattr(unreal.EditorLevelLibrary, "editor_end_play"):
            unreal.EditorLevelLibrary.editor_play_simulate()
            time.sleep(seconds)
            unreal.EditorLevelLibrary.editor_end_play()
            RESULT["pie_smoke_test"] = "passed_%s_seconds" % seconds
        else:
            RESULT["pie_smoke_test"] = "not_available_in_python_api"
            record_warning("PIE simulate API unavailable")
    except Exception as exc:
        RESULT["pie_smoke_test"] = "failed"
        record_error("run_pie_smoke_test", exc)


def main():
    RESULT["project_dir"] = project_dir()
    RESULT["worldforge_root"] = worldforge_root()
    make_content_dirs()
    materials = {
        "ground": create_material("M_WorldForge_Ground", unreal.LinearColor(0.12, 0.14, 0.12, 1.0)),
        "road": create_material("M_WorldForge_Road", unreal.LinearColor(0.035, 0.038, 0.045, 1.0)),
        "plaza": create_material("M_WorldForge_Plaza", unreal.LinearColor(0.22, 0.22, 0.18, 1.0)),
        "tower": create_material("M_WorldForge_Tower", unreal.LinearColor(0.08, 0.22, 0.34, 1.0)),
        "building": create_material("M_WorldForge_Building", unreal.LinearColor(0.16, 0.17, 0.20, 1.0)),
        "accent": create_material("M_WorldForge_Accent", unreal.LinearColor(0.20, 0.55, 0.85, 1.0)),
    }
    create_blueprint("BP_WorldForgeAgentDirector", "Tracks task name, status, execution stage, scene summary, last checkpoint, failure reason, and resource budget.")
    create_blueprint("BP_WorldForgeSafetyController", "Guards write operations, actor limits, WorldForgeManaged-only actions, and Content/WorldForge-only asset scope.")
    create_blueprint("BP_WorldForgeCheckpointManager", "Creates and restores WorldForgeManaged actor checkpoints without touching old content.")
    create_blueprint("BP_WorldForgeWorldProbe", "Reports map, WorldForge actor count, light rotation, task state, checkpoint, continuation status, and budget status.")
    create_blueprint("BP_WorldForgeCommandRouter", "Accepts only the WorldForge command whitelist and rejects arbitrary natural-language execution.")
    create_blueprint("BP_WorldForgeBlockoutBuilder", "Builds approved cube/plane/light blockouts within actor budget.")
    create_blueprint("BP_CodexControlActor", "Controlled Remote Control entry point; no console commands, arbitrary paths, file operations, or arbitrary deletes.")
    create_widget_blueprint()
    create_lab_map(materials)
    create_blockout_map(materials)
    write_text_plan()
    write_checkpoint()
    RESULT["world_summary_after_build"] = world_summary()
    if RESULT["world_summary_after_build"].get("worldforge_actor_count", 9999) <= 100:
        run_pie_smoke_test(20)
    create_remote_control_preset()
    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    except Exception as exc:
        record_warning("save_dirty_packages final: %s" % exc)
    RESULT["status"] = "completed_with_errors" if RESULT["errors"] else "completed"
    result_dir = out_path("06_性能与测试")
    ensure_os_dir(result_dir)
    result_path = os.path.join(result_dir, "worldforge_ue_build_result.json")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(RESULT, f, ensure_ascii=False, indent=2)
    unreal.log("WorldForge build result written to %s" % result_path)


if __name__ == "__main__":
    main()
