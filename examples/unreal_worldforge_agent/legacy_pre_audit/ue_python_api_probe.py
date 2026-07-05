# ruff: noqa
# fmt: off
import json
import os
import sys

import unreal


BASE = os.environ.get("CODEX_UE_BASE", r"<WORLDFORGE_ROOT>")
OUT_DIR = os.path.join(BASE, "99_临时文件")
os.makedirs(OUT_DIR, exist_ok=True)


def names(obj):
    try:
        return sorted([name for name in dir(obj) if not name.startswith("__")])
    except Exception as exc:
        return ["ERROR: %s" % exc]


classes = [
    "EditorAssetLibrary",
    "EditorLevelLibrary",
    "AssetToolsHelpers",
    "BlueprintFactory",
    "BlueprintEditorLibrary",
    "KismetCompilerLibrary",
    "WidgetBlueprintFactory",
    "RemoteControlPreset",
    "RemoteControlPresetFactory",
    "RemoteControlFunctionLibrary",
    "RemoteControlBlueprintLibrary",
    "RemoteControlExposeRegistry",
    "RemoteControlAPIBlueprintLibrary",
    "RemoteControlBinding",
    "RemoteControlProperty",
    "RemoteControlFunction",
    "Rotator",
    "Vector",
    "GameplayStatics",
    "SystemLibrary",
]

data = {
    "python": sys.version,
    "engine_version": unreal.SystemLibrary.get_engine_version(),
    "project_dir": unreal.Paths.project_dir(),
    "project_content_dir": unreal.Paths.project_content_dir(),
    "classes": {},
}

for cls_name in classes:
    obj = getattr(unreal, cls_name, None)
    data["classes"][cls_name] = {
        "exists": obj is not None,
        "dir": names(obj) if obj is not None else [],
    }

out_path = os.path.join(OUT_DIR, "ue_python_api_probe.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Codex UE Python API probe wrote: %s" % out_path)
