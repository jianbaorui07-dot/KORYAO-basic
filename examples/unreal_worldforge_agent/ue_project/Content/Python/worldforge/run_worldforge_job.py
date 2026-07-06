"""Run the WF-0009 WorldForge job from Unreal Editor Python."""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from worldforge import worldforge_preflight as preflight
from worldforge import worldforge_pie_verify
from worldforge import worldforge_preview
from worldforge import worldforge_receipt
from worldforge import worldforge_scene_builder
from worldforge import worldforge_spec_loader
from worldforge import worldforge_validation


def run(spec_path: str | None = None) -> dict:
    project_dir = preflight.get_project_dir()
    policy = preflight.load_resource_policy(project_dir)
    decision = preflight.evaluate_resource_mode(policy)
    probe = preflight.probe_project(project_dir)
    if not decision["allowed"]:
        report = worldforge_validation.validate_filesystem(project_dir)
        worldforge_validation.write_validation(project_dir, report)
        receipt = {
            "job_id": "WF0009_v0.9-real",
            "status": "blocked",
            "blocked_by": "resource_policy",
            "decision": decision,
            "project_probe": probe,
            "ue_started_for_build": True,
            "map_created": False,
            "blueprints_created": [],
            "materials_created": [],
            "pie_verified": False,
            "preview_generated": False,
            "completion": "not_completed",
        }
        worldforge_receipt.write_receipt(project_dir, receipt)
        return receipt

    spec_file = Path(spec_path) if spec_path else worldforge_spec_loader.default_spec_path(project_dir)
    spec = worldforge_spec_loader.load_worldspec(spec_file)
    build_result = worldforge_scene_builder.build_scene(spec)
    validation = worldforge_validation.validate_unreal_assets()
    worldforge_validation.write_validation(project_dir, validation)
    pie = {"attempted": False, "reason": "Resource mode below PIE threshold."}
    if decision["mode"] in ("pie_verify", "cinematic_render"):
        pie = worldforge_pie_verify.run_short_pie(max_seconds=45)
    preview = {"created": False, "reason": "Skipped unless cinematic threshold is reached."}
    if decision["mode"] == "cinematic_render":
        preview = worldforge_preview.take_editor_preview(project_dir)
    receipt = {
        "job_id": "WF0009_v0.9-real",
        "status": "partial_built_pending_pie" if validation["complete"] else "partial_assets_missing",
        "decision": decision,
        "project_probe": probe,
        "worldspec": str(spec_file),
        "build_result": build_result,
        "validation": validation,
        "preview": preview,
        "pie": pie,
        "pie_verified": bool(pie.get("started")),
        "player_movement_verified": bool(pie.get("player_movement_verified")),
        "interaction_verified": bool(pie.get("interaction_verified")),
        "completion": "not_completed",
    }
    worldforge_receipt.write_receipt(project_dir, receipt)
    return receipt


if __name__ == "__main__":
    result = run(sys.argv[1] if len(sys.argv) > 1 else None)
    print(result)
