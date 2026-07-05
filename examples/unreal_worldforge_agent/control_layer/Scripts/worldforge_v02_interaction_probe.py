# ruff: noqa
# fmt: off
import json
import os
import traceback

import unreal


MAP_PATH = "/Game/WorldForge/Maps/M_WorldForgeBlockoutSandbox"
TAG = "WorldForgeManaged"
RESULT = {
    "status": "started",
    "errors": [],
    "warnings": [],
    "map_loaded": None,
    "world_summary": {},
    "blueprints": {},
    "actors": {},
    "api_capabilities": {},
    "enhanced_input": {},
}


def worldforge_root():
    return os.path.dirname(os.path.normpath(unreal.Paths.project_dir()))


def out_path():
    return os.path.join(
        worldforge_root(),
        "03_WorldForge控制层",
        "Logs",
        "WorldForge_v02_interaction_probe.json",
    )


def warn(message):
    RESULT["warnings"].append(message)
    unreal.log_warning("WorldForge v0.2 probe warning: %s" % message)


def err(label, exc):
    RESULT["errors"].append(
        {"label": label, "error": str(exc), "traceback": traceback.format_exc()}
    )
    unreal.log_error("WorldForge v0.2 probe error in %s: %s" % (label, exc))


def bool_has(name):
    return getattr(unreal, name, None) is not None


def safe_class_name(obj):
    try:
        return str(obj.get_class().get_name())
    except Exception:
        return str(type(obj))


def load_map():
    try:
        ok = unreal.EditorLevelLibrary.load_level(MAP_PATH)
        RESULT["map_loaded"] = bool(ok)
    except Exception as exc:
        err("load_map", exc)


def actor_tags(actor):
    try:
        return [str(t) for t in actor.get_editor_property("tags")]
    except Exception:
        return []


def collect_world():
    try:
        actors = unreal.EditorLevelLibrary.get_all_level_actors()
        worldforge = []
        labels = []
        classes = {}
        for actor in actors:
            label = actor.get_actor_label()
            labels.append(label)
            tags = actor_tags(actor)
            classes[label] = {
                "class": safe_class_name(actor),
                "tags": tags,
                "location": [
                    round(actor.get_actor_location().x, 3),
                    round(actor.get_actor_location().y, 3),
                    round(actor.get_actor_location().z, 3),
                ],
            }
            if TAG in tags:
                worldforge.append(label)
        RESULT["world_summary"] = {
            "map": str(unreal.EditorLevelLibrary.get_editor_world().get_name()),
            "total_actor_count": len(actors),
            "worldforge_actor_count": len(worldforge),
            "worldforge_actor_labels": worldforge,
        }
        RESULT["actors"] = classes
    except Exception as exc:
        err("collect_world", exc)


def inspect_blueprint(asset_path):
    data = {"asset_path": asset_path, "exists": False}
    try:
        data["exists"] = unreal.EditorAssetLibrary.does_asset_exist(asset_path)
        if not data["exists"]:
            return data
        asset = unreal.EditorAssetLibrary.load_asset(asset_path)
        data["class"] = safe_class_name(asset)
        try:
            parent = asset.get_editor_property("parent_class")
            data["parent_class"] = str(parent.get_name()) if parent else None
        except Exception as exc:
            data["parent_class_error"] = str(exc)
        try:
            generated = asset.generated_class()
            data["generated_class"] = str(generated.get_name()) if generated else None
        except Exception as exc:
            data["generated_class_error"] = str(exc)
        try:
            subobjects = []
            for component in asset.get_editor_property("simple_construction_script").get_all_nodes():
                subobjects.append(str(component.get_variable_name()))
            data["sCS_nodes"] = subobjects
        except Exception as exc:
            data["sCS_nodes_error"] = str(exc)
        if bool_has("BlueprintEditorLibrary"):
            try:
                graphs = unreal.BlueprintEditorLibrary.get_all_graphs(asset)
                data["graphs"] = [str(g.get_name()) for g in graphs]
            except Exception as exc:
                data["graphs_error"] = str(exc)
        return data
    except Exception as exc:
        err("inspect_blueprint " + asset_path, exc)
        data["fatal_error"] = str(exc)
        return data


def collect_blueprints():
    paths = [
        "/Game/WorldForge/Blueprints/BP_WorldForgeExplorerPawn",
        "/Game/WorldForge/Blueprints/BP_WorldForgeCityMoodController",
        "/Game/WorldForge/Blueprints/BP_WorldForgeOfflineTaskRunner",
        "/Game/WorldForge/Blueprints/BP_WorldForgeCheckpointManager",
        "/Game/WorldForge/EditorTools/EUW_WorldForgeControlDesk",
        "/Game/WorldForge/UI/WBP_WorldForgeStatus",
    ]
    for path in paths:
        RESULT["blueprints"][path] = inspect_blueprint(path)


def inspect_apis():
    names = [
        "BlueprintEditorLibrary",
        "BlueprintEditorSubsystem",
        "KismetCompilerLibrary",
        "K2Node_InputKey",
        "K2Node_InputAction",
        "K2Node_CallFunction",
        "K2Node_Event",
        "K2Node_CustomEvent",
        "K2Node_VariableGet",
        "K2Node_VariableSet",
        "EdGraph",
        "EdGraphSchema_K2",
        "WidgetBlueprintFactory",
        "EditorUtilityWidgetBlueprintFactory",
        "InputAction",
        "InputMappingContext",
        "EnhancedInputComponent",
        "EnhancedInputSubsystems",
        "InputKeySelector",
        "PlayerController",
        "GameModeBase",
    ]
    RESULT["api_capabilities"] = {name: bool_has(name) for name in names}
    try:
        plugins = unreal.Plugins.get_enabled_plugin_names()
        RESULT["enhanced_input"]["enabled_plugins_containing_input"] = [
            p for p in plugins if "Input" in p or "input" in p
        ]
    except Exception as exc:
        RESULT["enhanced_input"]["plugin_query_error"] = str(exc)


def write_result():
    try:
        os.makedirs(os.path.dirname(out_path()), exist_ok=True)
        RESULT["status"] = "completed" if not RESULT["errors"] else "completed_with_errors"
        with open(out_path(), "w", encoding="utf-8") as f:
            json.dump(RESULT, f, ensure_ascii=False, indent=2)
        unreal.log("WorldForge v0.2 interaction probe wrote %s" % out_path())
    except Exception as exc:
        unreal.log_error("WorldForge v0.2 probe failed to write result: %s" % exc)


def main():
    try:
        load_map()
        collect_world()
        collect_blueprints()
        inspect_apis()
        write_result()
    finally:
        try:
            unreal.SystemLibrary.quit_editor()
        except Exception as exc:
            warn("quit_editor failed: %s" % exc)


main()
