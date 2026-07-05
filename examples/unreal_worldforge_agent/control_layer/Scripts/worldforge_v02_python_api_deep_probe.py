# ruff: noqa
# fmt: off
import json
import os
import unreal


def worldforge_root():
    return os.path.dirname(os.path.normpath(unreal.Paths.project_dir()))


def out_path():
    return os.path.join(
        worldforge_root(),
        "03_WorldForge控制层",
        "Logs",
        "WorldForge_v02_python_api_deep_probe.json",
    )


def safe_dir(obj):
    try:
        return [name for name in dir(obj) if not name.startswith("_")]
    except Exception as exc:
        return ["DIR_ERROR: %s" % exc]


def main():
    targets = [
        "BlueprintEditorLibrary",
        "EditorAssetLibrary",
        "EditorLevelLibrary",
        "EditorUtilityLibrary",
        "EditorLoadingAndSavingUtils",
        "AssetToolsHelpers",
        "InputAction",
        "InputMappingContext",
        "EnhancedInputComponent",
        "UserWidget",
        "Button",
        "TextBlock",
        "WidgetTree",
        "KismetSystemLibrary",
        "GameplayStatics",
    ]
    result = {
        "status": "completed",
        "matching_unreal_names": [
            name
            for name in dir(unreal)
            if any(token in name.lower() for token in ["blueprint", "graph", "k2", "input", "widget", "key"])
        ],
        "target_methods": {},
    }
    for target in targets:
        obj = getattr(unreal, target, None)
        result["target_methods"][target] = {
            "exists": obj is not None,
            "methods": safe_dir(obj) if obj is not None else [],
        }
    os.makedirs(os.path.dirname(out_path()), exist_ok=True)
    with open(out_path(), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    unreal.log("WorldForge v0.2 API deep probe wrote %s" % out_path())
    unreal.SystemLibrary.quit_editor()


main()
