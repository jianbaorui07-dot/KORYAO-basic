from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    root = project_root()
    state_path = root / "Saved" / "WorldForge" / "run_state.json"
    runtime_state_path = root / "runtime" / "run_state.json"
    baseline_path = root / "Saved" / "WorldForge" / "Baselines" / "WF0009_R1_MAP_VALIDATED.json"
    golden_path = root / "Saved" / "WorldForge" / "GoldenSamples" / "WF0009_GoldenSample.json"
    preview_path = Path(r"<WORLDFORGE_RUNTIME>\Previews\WF0009_SnowTemple_Micro_R1_preview.png")
    recipe_0009 = root / "Content" / "Python" / "WorldForge" / "Recipes" / "WF0009_SnowTemple_R1.json"
    recipe_0010 = root / "Content" / "Python" / "WorldForge" / "Recipes" / "WF0010_DNABonsaiWorkshop_R1.json"

    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    recipe = json.loads(recipe_0009.read_text(encoding="utf-8"))
    old = json.loads(golden_path.read_text(encoding="utf-8")) if golden_path.exists() else None
    now = datetime.now().astimezone().isoformat()

    golden = {
        "scene_id": "WF0009",
        "scene_name": "SnowTemple Micro",
        "map_asset_path": baseline["map_asset_path"],
        "map_disk_path": baseline["map_disk_path"],
        "actor_count": int(baseline["actor_count"]),
        "preview_path": str(preview_path),
        "validation_receipt_path": baseline["validation_receipt_path"],
        "framework_version": "1.0.0",
        "recipe_version": recipe.get("recipe_version", "1.0.0"),
        "created_at": old["created_at"] if old else now,
        "last_verified_at": now,
        "baseline_path": str(baseline_path),
        "recipe_path": str(recipe_0009),
        "last_known_good": True,
    }
    write_json(golden_path, golden)

    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    state.update(
        {
            "phase": "FRAMEWORK_READY",
            "framework_version": "1.0.0",
            "active_scene_id": "WF0009",
            "active_recipe_path": str(recipe_0009),
            "golden_sample_path": str(golden_path),
            "golden_samples": [str(golden_path)],
            "recipes": [str(recipe_0009), str(recipe_0010)],
            "core_modules": [
                "resource_policy.py",
                "state_manager.py",
                "receipt_manager.py",
                "map_builder.py",
                "actor_factory.py",
                "camera_preview.py",
                "editor_launcher.py",
                "recovery_manager.py",
                "scene_validator.py",
            ],
            "requested_map_path": baseline["map_asset_path"],
            "actual_map_exists": Path(baseline["map_disk_path"]).exists(),
            "actual_actor_count": int(baseline["actor_count"]),
            "validation_receipt_path": baseline["validation_receipt_path"],
            "baseline_path": str(baseline_path),
            "preview_exists": preview_path.exists(),
            "preview_path": str(preview_path),
            "ue_process_running": False,
            "ue_pid": None,
            "source_of_truth": str(state_path),
            "runtime_state_role": "compatibility_mirror_only",
            "last_error": "",
            "updated_at": now,
        }
    )
    write_json(state_path, state)

    mirror = dict(state)
    mirror["compatibility_mirror_of"] = str(state_path)
    mirror["mirror_note"] = "Saved\\WorldForge\\run_state.json is the only authoritative state file."
    write_json(runtime_state_path, mirror)

    print(json.dumps({"golden_sample": str(golden_path), "phase": state["phase"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
