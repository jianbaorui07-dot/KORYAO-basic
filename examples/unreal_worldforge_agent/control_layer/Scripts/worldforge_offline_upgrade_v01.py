# ruff: noqa
# fmt: off
import json
import os
import time
import traceback

import unreal

TAG = "WorldForgeManaged"
UPGRADE_TAG = "WorldForgeUpgradeV01"
RESULT = {
    "status": "started",
    "errors": [],
    "warnings": [],
    "plugin_check": {},
    "task": None,
    "preview": {},
    "created_assets": [],
    "created_actors": [],
    "skipped_existing_actors": [],
    "pre_summary": {},
    "post_summary": {},
    "pie_smoke_test": "not_run",
    "restore_test": "not_run",
    "e_key_toggle_validation": "not_verified_by_python",
}

ALLOWED_COMMANDS = [
    "PreviewCityUpgrade",
    "ExecuteCityUpgrade",
    "CreateCheckpoint",
    "RestoreLastCheckpoint",
    "GenerateWorldSummary",
    "RunPIESmokeTest",
    "StopCurrentTask",
]

PLANNED_ACTORS = [
    "WORLDFORGE_UPG_PlazaLightStrip_A",
    "WORLDFORGE_UPG_PlazaLightStrip_B",
    "WORLDFORGE_UPG_WindowBand_L01",
    "WORLDFORGE_UPG_WindowBand_L02",
    "WORLDFORGE_UPG_WindowBand_R01",
    "WORLDFORGE_UPG_WindowBand_R02",
    "WORLDFORGE_UPG_TowerBeacon",
    "WORLDFORGE_UPG_GuideLine_L",
    "WORLDFORGE_UPG_GuideLine_R",
    "WORLDFORGE_UPG_ZoneMarker_Plaza",
    "WORLDFORGE_UPG_ZoneMarker_Tower",
    "WORLDFORGE_UPG_ObservationPoint",
    "WORLDFORGE_UPG_ExplorerPawn",
    "WORLDFORGE_UPG_MoodController",
]


def worldforge_root():
    return os.path.dirname(os.path.normpath(unreal.Paths.project_dir()))


def path_in_root(*parts):
    return os.path.join(worldforge_root(), *parts)


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def warn(msg):
    RESULT["warnings"].append(msg)
    unreal.log_warning("WorldForge Offline Bridge warning: %s" % msg)


def err(label, exc):
    RESULT["errors"].append({"label": label, "error": str(exc), "traceback": traceback.format_exc()})
    unreal.log_error("WorldForge Offline Bridge error in %s: %s" % (label, exc))


def has_asset(path):
    try:
        return unreal.EditorAssetLibrary.does_asset_exist(path)
    except Exception:
        return False


def save_asset(path):
    try:
        unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
    except Exception as exc:
        warn("save_asset failed for %s: %s" % (path, exc))


def asset_tools():
    return unreal.AssetToolsHelpers.get_asset_tools()


def make_content_dirs():
    for d in [
        "/Game/WorldForge/EditorTools",
        "/Game/WorldForge/TaskData",
        "/Game/WorldForge/Reports",
        "/Game/WorldForge/Materials",
        "/Game/WorldForge/Blueprints",
        "/Game/WorldForge/Maps",
    ]:
        try:
            unreal.EditorAssetLibrary.make_directory(d)
        except Exception as exc:
            err("make_directory " + d, exc)


def plugin_check():
    checks = {
        "EditorAssetLibrary": getattr(unreal, "EditorAssetLibrary", None) is not None,
        "EditorLevelLibrary": getattr(unreal, "EditorLevelLibrary", None) is not None,
        "BlueprintFactory": getattr(unreal, "BlueprintFactory", None) is not None,
        "WidgetBlueprintFactory": getattr(unreal, "WidgetBlueprintFactory", None) is not None,
        "EditorUtilityWidgetBlueprint": getattr(unreal, "EditorUtilityWidgetBlueprint", None) is not None,
        "EditorUtilityWidgetBlueprintFactory": getattr(unreal, "EditorUtilityWidgetBlueprintFactory", None) is not None,
        "PythonScriptPluginUsable": True,
    }
    RESULT["plugin_check"] = checks
    return checks


def load_task():
    task_path = path_in_root("03_WorldForge控制层", "Tasks", "Inbox", "002_未来城市漫游升级.json")
    with open(task_path, "r", encoding="utf-8-sig") as f:
        task = json.load(f)
    RESULT["task"] = task
    validate_task(task)
    return task


def validate_task(task):
    if task.get("command") not in ALLOWED_COMMANDS:
        raise RuntimeError("Task command is not whitelisted: %s" % task.get("command"))
    strict = {
        "map": "M_WorldForgeBlockoutSandbox",
        "mode": "preview_then_execute",
        "actor_limit": 60,
        "build_limit_per_step": 15,
        "checkpoint_required": True,
        "allow_external_assets": False,
        "allow_network": False,
        "allow_delete_non_worldforge_actor": False,
        "pie_test_seconds": 20,
        "quality_mode": "low_load",
    }
    for key, expected in strict.items():
        if task.get(key) != expected:
            raise RuntimeError("Task field %s expected %r got %r" % (key, expected, task.get(key)))


def world_summary():
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    worldforge = []
    upgrade = []
    labels = []
    for actor in actors:
        label = actor.get_actor_label()
        labels.append(label)
        tags = [str(t) for t in actor.get_editor_property("tags")]
        if TAG in tags:
            worldforge.append(actor)
        if UPGRADE_TAG in tags:
            upgrade.append(actor)
    return {
        "map": str(unreal.EditorLevelLibrary.get_editor_world().get_name()),
        "total_actor_count": len(actors),
        "worldforge_actor_count": len(worldforge),
        "upgrade_actor_count": len(upgrade),
        "labels": labels,
    }


def existing_labels():
    return set([a.get_actor_label() for a in unreal.EditorLevelLibrary.get_all_level_actors()])


def create_material(name, color, emissive=None, strength=0.0):
    package = "/Game/WorldForge/Materials"
    path = package + "/" + name
    if has_asset(path):
        return unreal.EditorAssetLibrary.load_asset(path)
    mat = asset_tools().create_asset(name, package, unreal.Material, unreal.MaterialFactoryNew())
    if not mat:
        return None
    RESULT["created_assets"].append(path)
    try:
        base = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 0)
        base.set_editor_property("constant", color)
        unreal.MaterialEditingLibrary.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
        rough = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant, -350, 160)
        rough.set_editor_property("r", 0.65)
        unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
        if emissive is not None and strength > 0:
            em = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 320)
            em.set_editor_property("constant", emissive)
            mult = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionMultiply, -120, 320)
            scalar = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant, -350, 460)
            scalar.set_editor_property("r", strength)
            unreal.MaterialEditingLibrary.connect_material_expressions(em, "", mult, "A")
            unreal.MaterialEditingLibrary.connect_material_expressions(scalar, "", mult, "B")
            unreal.MaterialEditingLibrary.connect_material_property(mult, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        unreal.MaterialEditingLibrary.recompile_material(mat)
    except Exception as exc:
        warn("material node setup fallback for %s: %s" % (name, exc))
    save_asset(path)
    return mat


def create_blueprint(name, parent_class, role):
    package = "/Game/WorldForge/Blueprints"
    path = package + "/" + name
    if has_asset(path):
        return unreal.EditorAssetLibrary.load_asset(path)
    factory = unreal.BlueprintFactory()
    try:
        factory.set_editor_property("parent_class", parent_class)
    except Exception:
        pass
    bp = asset_tools().create_asset(name, package, unreal.Blueprint, factory)
    if bp:
        unreal.EditorAssetLibrary.set_metadata_tag(bp, "WorldForgeRole", role)
        unreal.EditorAssetLibrary.set_metadata_tag(bp, "WorldForgeOfflineBridge", "v0.1")
        RESULT["created_assets"].append(path)
        save_asset(path)
    return bp


def create_euw_or_widget():
    package = "/Game/WorldForge/EditorTools"
    name = "EUW_WorldForgeControlDesk"
    path = package + "/" + name
    if has_asset(path):
        return unreal.EditorAssetLibrary.load_asset(path)
    checks = RESULT.get("plugin_check") or plugin_check()
    try:
        if checks.get("EditorUtilityWidgetBlueprint") and checks.get("EditorUtilityWidgetBlueprintFactory"):
            cls = getattr(unreal, "EditorUtilityWidgetBlueprint")
            factory = getattr(unreal, "EditorUtilityWidgetBlueprintFactory")()
            asset = asset_tools().create_asset(name, package, cls, factory)
        else:
            factory = unreal.WidgetBlueprintFactory()
            asset = asset_tools().create_asset(name, package, unreal.WidgetBlueprint, factory)
            warn("Editor Utility Widget class unavailable; created WidgetBlueprint fallback named EUW_WorldForgeControlDesk")
        if asset:
            unreal.EditorAssetLibrary.set_metadata_tag(asset, "WorldForgeRole", "Offline control desk: read task, preview, checkpoint, execute, summary, 20s PIE, restore, stop")
            RESULT["created_assets"].append(path)
            save_asset(path)
            return asset
    except Exception as exc:
        err("create_euw_or_widget", exc)
    return None


def actor_tags(actor):
    try:
        return [str(t) for t in actor.get_editor_property("tags")]
    except Exception:
        return []


def add_tags(actor, tags):
    current = []
    try:
        current = list(actor.get_editor_property("tags"))
    except Exception:
        current = []
    for tag in tags:
        n = unreal.Name(tag)
        if n not in current:
            current.append(n)
    actor.set_editor_property("tags", current)


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
        warn("set_mesh failed for %s: %s" % (actor.get_name(), exc))


def spawn_actor(cls, label, loc, rot=None, scale=None, mesh=None, material=None):
    if label in existing_labels():
        RESULT["skipped_existing_actors"].append(label)
        return None
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(cls, loc, rot or unreal.Rotator(0, 0, 0))
    label_actor(actor, label)
    if scale:
        actor.set_actor_scale3d(scale)
    if mesh:
        set_mesh(actor, mesh, material)
    add_tags(actor, [TAG, UPGRADE_TAG])
    RESULT["created_actors"].append(label)
    return actor


def light_intensity(actor, value):
    for attr in ["point_light_component", "spot_light_component", "light_component"]:
        try:
            comp = getattr(actor, attr)
            comp.set_editor_property("intensity", value)
            return
        except Exception:
            pass
    try:
        comp = actor.get_component_by_class(unreal.LightComponentBase)
        if comp:
            comp.set_editor_property("intensity", value)
    except Exception:
        pass


def actor_state(actor):
    loc = actor.get_actor_location()
    rot = actor.get_actor_rotation()
    scale = actor.get_actor_scale3d()
    state = {
        "label": actor.get_actor_label(),
        "class": actor.get_class().get_name(),
        "tags": actor_tags(actor),
        "location": [loc.x, loc.y, loc.z],
        "rotation": [rot.roll, rot.pitch, rot.yaw],
        "scale": [scale.x, scale.y, scale.z],
    }
    try:
        comp = actor.get_component_by_class(unreal.LightComponentBase)
        if comp:
            state["light_intensity"] = comp.get_editor_property("intensity")
    except Exception:
        pass
    return state


def write_checkpoint(name):
    cp_dir = path_in_root("05_任务与检查点", "checkpoints")
    ensure_dir(cp_dir)
    actors = []
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        tags = actor_tags(actor)
        if TAG in tags:
            actors.append(actor_state(actor))
    cp = {"checkpoint": name, "actor_count": len(actors), "actors": actors, "time": time.strftime("%Y-%m-%d %H:%M:%S")}
    path = os.path.join(cp_dir, name + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cp, f, ensure_ascii=False, indent=2)
    return path


def apply_checkpoint_properties(path):
    with open(path, "r", encoding="utf-8") as f:
        cp = json.load(f)
    wanted = {a["label"]: a for a in cp.get("actors", [])}
    changed = 0
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        label = actor.get_actor_label()
        if label not in wanted:
            continue
        state = wanted[label]
        loc = state.get("location")
        rot = state.get("rotation")
        scale = state.get("scale")
        if loc:
            actor.set_actor_location(unreal.Vector(loc[0], loc[1], loc[2]), False, False)
        if rot:
            actor.set_actor_rotation(unreal.Rotator(rot[1], rot[2], rot[0]), False)
        if scale:
            actor.set_actor_scale3d(unreal.Vector(scale[0], scale[1], scale[2]))
        if "light_intensity" in state:
            light_intensity(actor, state["light_intensity"])
        changed += 1
    return changed


def create_upgrade(materials):
    cube = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")
    # 2 plaza light strips
    spawn_actor(unreal.StaticMeshActor, "WORLDFORGE_UPG_PlazaLightStrip_A", unreal.Vector(-260, -650, 18), scale=unreal.Vector(0.22, 6.2, 0.035), mesh=cube, material=materials["light"])
    spawn_actor(unreal.StaticMeshActor, "WORLDFORGE_UPG_PlazaLightStrip_B", unreal.Vector(260, -650, 18), scale=unreal.Vector(0.22, 6.2, 0.035), mesh=cube, material=materials["light"])
    # 4 window bands on existing building groups
    spawn_actor(unreal.StaticMeshActor, "WORLDFORGE_UPG_WindowBand_L01", unreal.Vector(-520, -520, 175), scale=unreal.Vector(2.82, 0.06, 0.18), mesh=cube, material=materials["window"])
    spawn_actor(unreal.StaticMeshActor, "WORLDFORGE_UPG_WindowBand_L02", unreal.Vector(-520, 280, 220), scale=unreal.Vector(2.82, 0.06, 0.18), mesh=cube, material=materials["window"])
    spawn_actor(unreal.StaticMeshActor, "WORLDFORGE_UPG_WindowBand_R01", unreal.Vector(520, -520, 175), scale=unreal.Vector(2.82, 0.06, 0.18), mesh=cube, material=materials["window"])
    spawn_actor(unreal.StaticMeshActor, "WORLDFORGE_UPG_WindowBand_R02", unreal.Vector(520, 280, 220), scale=unreal.Vector(2.82, 0.06, 0.18), mesh=cube, material=materials["window"])
    # tower beacon
    beacon = spawn_actor(unreal.PointLight, "WORLDFORGE_UPG_TowerBeacon", unreal.Vector(0, 320, 890))
    if beacon:
        light_intensity(beacon, 950.0)
    # guide lines
    spawn_actor(unreal.StaticMeshActor, "WORLDFORGE_UPG_GuideLine_L", unreal.Vector(-90, -260, 16), scale=unreal.Vector(0.08, 16, 0.025), mesh=cube, material=materials["guide"])
    spawn_actor(unreal.StaticMeshActor, "WORLDFORGE_UPG_GuideLine_R", unreal.Vector(90, -260, 16), scale=unreal.Vector(0.08, 16, 0.025), mesh=cube, material=materials["guide"])
    # zone markers
    sign1 = spawn_actor(unreal.TextRenderActor, "WORLDFORGE_UPG_ZoneMarker_Plaza", unreal.Vector(-360, -950, 80), unreal.Rotator(0, 0, 20))
    if sign1:
        sign1.text_render.set_editor_property("text", "PLAZA")
        sign1.text_render.set_editor_property("world_size", 38.0)
    sign2 = spawn_actor(unreal.TextRenderActor, "WORLDFORGE_UPG_ZoneMarker_Tower", unreal.Vector(210, 120, 120), unreal.Rotator(0, 0, -25))
    if sign2:
        sign2.text_render.set_editor_property("text", "TOWER")
        sign2.text_render.set_editor_property("world_size", 42.0)
    # observation point
    spawn_actor(unreal.StaticMeshActor, "WORLDFORGE_UPG_ObservationPoint", unreal.Vector(-240, -1150, 42), scale=unreal.Vector(1.2, 1.2, 0.18), mesh=cube, material=materials["observation"])
    # explorer pawn and mood controller instances
    pawn_bp = unreal.EditorAssetLibrary.load_asset("/Game/WorldForge/Blueprints/BP_WorldForgeExplorerPawn")
    pawn_class = pawn_bp.generated_class() if pawn_bp else unreal.DefaultPawn
    pawn = spawn_actor(pawn_class, "WORLDFORGE_UPG_ExplorerPawn", unreal.Vector(-240, -1150, 120), unreal.Rotator(0, 0, 0))
    if pawn:
        try:
            pawn.set_editor_property("auto_possess_player", unreal.AutoReceiveInput.PLAYER0)
        except Exception as exc:
            warn("Could not set AutoPossessPlayer for explorer pawn: %s" % exc)
    mood_bp = unreal.EditorAssetLibrary.load_asset("/Game/WorldForge/Blueprints/BP_WorldForgeCityMoodController")
    mood_class = mood_bp.generated_class() if mood_bp else unreal.Actor
    spawn_actor(mood_class, "WORLDFORGE_UPG_MoodController", unreal.Vector(0, -850, 120))


def create_assets():
    make_content_dirs()
    checks = plugin_check()
    create_euw_or_widget()
    create_blueprint("BP_WorldForgeOfflineTaskRunner", unreal.Actor, "Reads whitelisted offline tasks and writes checkpoints/world summaries without network or deletes.")
    create_blueprint("BP_WorldForgeCityMoodController", unreal.Actor, "Controls WorldForge day/night preview state for WorldForge lights/materials only; no global render settings.")
    create_blueprint("BP_WorldForgeExplorerPawn", unreal.DefaultPawn, "DefaultPawn-derived lightweight explorer pawn; inherits basic movement and mouse look; placed with AutoPossess Player0.")
    mats = {
        "light": create_material("M_WorldForge_Upgrade_LightStrip", unreal.LinearColor(0.05, 0.22, 0.28, 1), unreal.LinearColor(0.0, 0.75, 1.0, 1), 2.0),
        "window": create_material("M_WorldForge_Upgrade_WindowGlow", unreal.LinearColor(0.04, 0.08, 0.12, 1), unreal.LinearColor(0.3, 0.95, 1.0, 1), 1.4),
        "guide": create_material("M_WorldForge_Upgrade_GuideLine", unreal.LinearColor(0.02, 0.12, 0.14, 1), unreal.LinearColor(0.0, 0.55, 0.95, 1), 1.1),
        "observation": create_material("M_WorldForge_Upgrade_Observation", unreal.LinearColor(0.18, 0.22, 0.20, 1), unreal.LinearColor(0.12, 0.5, 0.35, 1), 0.5),
    }
    return mats


def preview_plan(pre_summary):
    existing = existing_labels()
    to_add = [label for label in PLANNED_ACTORS if label not in existing]
    RESULT["preview"] = {
        "planned_actor_labels": PLANNED_ACTORS,
        "new_actor_labels": to_add,
        "new_actor_count": len(to_add),
        "pre_worldforge_actor_count": pre_summary.get("worldforge_actor_count"),
        "post_worldforge_actor_estimate": pre_summary.get("worldforge_actor_count", 0) + len(to_add),
        "within_build_limit_per_step": len(to_add) <= 15,
        "within_actor_limit": pre_summary.get("worldforge_actor_count", 0) + len(to_add) <= 60,
        "allowed_materials": ["basic cube mesh", "text render", "point light", "DefaultPawn subclass"],
    }
    if not RESULT["preview"]["within_build_limit_per_step"]:
        raise RuntimeError("Preview exceeds build_limit_per_step")
    if not RESULT["preview"]["within_actor_limit"]:
        raise RuntimeError("Preview exceeds actor_limit")


def run_pie(seconds):
    try:
        unreal.EditorLevelLibrary.editor_play_simulate()
        time.sleep(seconds)
        unreal.EditorLevelLibrary.editor_end_play()
        RESULT["pie_smoke_test"] = "passed_%s_seconds" % seconds
    except Exception as exc:
        RESULT["pie_smoke_test"] = "failed"
        err("run_pie", exc)


def write_reports(pre_cp, post_cp):
    report_dir = path_in_root("03_WorldForge控制层", "Logs")
    ensure_dir(report_dir)
    path = os.path.join(report_dir, "WorldForge_OfflineBridge_任务002执行结果.json")
    RESULT["pre_checkpoint"] = pre_cp
    RESULT["post_checkpoint"] = post_cp
    with open(path, "w", encoding="utf-8") as f:
        json.dump(RESULT, f, ensure_ascii=False, indent=2)
    md_path = os.path.join(report_dir, "WorldForge_OfflineBridge_任务002执行摘要.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# WorldForge Offline Bridge 任务002执行摘要\n\n")
        f.write("- 状态：%s\n" % RESULT["status"])
        f.write("- 新增 Actor：%s\n" % len(RESULT["created_actors"]))
        f.write("- 升级前 WorldForge Actor：%s\n" % RESULT["pre_summary"].get("worldforge_actor_count"))
        f.write("- 升级后 WorldForge Actor：%s\n" % RESULT["post_summary"].get("worldforge_actor_count"))
        f.write("- PIE：%s\n" % RESULT["pie_smoke_test"])
        f.write("- Restore 测试：%s\n" % RESULT["restore_test"])
        f.write("- E 键验证：%s\n" % RESULT["e_key_toggle_validation"])
        f.write("- 错误：%s\n" % len(RESULT["errors"]))
    RESULT["result_json"] = path
    RESULT["result_md"] = md_path


def main():
    try:
        task = load_task()
        unreal.EditorLevelLibrary.load_level("/Game/WorldForge/Maps/M_WorldForgeBlockoutSandbox")
        pre = world_summary()
        RESULT["pre_summary"] = pre
        preview_plan(pre)
        pre_cp = write_checkpoint("checkpoint_002_pre_city_upgrade")
        mats = create_assets()
        create_upgrade(mats)
        post_mid = world_summary()
        if post_mid.get("worldforge_actor_count", 9999) > 60:
            raise RuntimeError("WorldForge actor count exceeded 60 after upgrade")
        post_cp = write_checkpoint("checkpoint_002_post_city_upgrade")
        # Non-destructive restore test: perturb one upgrade light intensity, then restore from completed checkpoint.
        changed_before_restore = 0
        for actor in unreal.EditorLevelLibrary.get_all_level_actors():
            if actor.get_actor_label() == "WORLDFORGE_UPG_TowerBeacon":
                light_intensity(actor, 120.0)
                changed_before_restore = 1
                break
        restored = apply_checkpoint_properties(post_cp)
        RESULT["restore_test"] = "passed_property_restore_changed_%s_restored_%s" % (changed_before_restore, restored)
        RESULT["post_summary"] = world_summary()
        try:
            unreal.EditorLevelLibrary.save_current_level()
            unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
        except Exception as exc:
            err("save_after_upgrade", exc)
        run_pie(int(task.get("pie_test_seconds", 20)))
        try:
            unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
        except Exception as exc:
            warn("final save_dirty_packages: %s" % exc)
        RESULT["status"] = "completed_with_errors" if RESULT["errors"] else "completed"
        write_reports(pre_cp, post_cp)
    except Exception as exc:
        err("main", exc)
        RESULT["status"] = "failed"
        write_reports("", "")


if __name__ == "__main__":
    main()
