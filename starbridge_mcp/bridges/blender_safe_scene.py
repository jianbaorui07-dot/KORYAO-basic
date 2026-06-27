from __future__ import annotations

from typing import Any

from starbridge_mcp.core.security import sanitize


def build_scene_plan(
    *,
    scene_name: str = "starbridge_public_scene",
    render_width: int = 1280,
    render_height: int = 720,
) -> dict[str, Any]:
    width = max(320, min(int(render_width), 4096))
    height = max(240, min(int(render_height), 4096))
    name = scene_name.strip() or "starbridge_public_scene"
    return sanitize(
        {
            "ok": True,
            "bridge": "blender",
            "action": "scene_plan",
            "mode": "dry_run",
            "scene": {
                "name": name,
                "units": "metric",
                "render": {
                    "width": width,
                    "height": height,
                    "engine": "Eevee or Workbench",
                    "output_policy": "ignored_output_directory_only",
                },
                "objects": [
                    {"name": "ground_grid", "type": "plane", "source": "primitive"},
                    {"name": "center_cube", "type": "cube", "source": "primitive"},
                    {"name": "orbit_sphere", "type": "uv_sphere", "source": "primitive"},
                    {"name": "axis_beacons", "type": "cylinders", "source": "primitive"},
                ],
                "materials": [
                    {"name": "mat_grid_neutral", "type": "built_in_principled"},
                    {"name": "mat_starbridge_blue", "type": "built_in_principled"},
                    {"name": "mat_safety_green", "type": "built_in_principled"},
                ],
                "lights": [
                    {"name": "key_area_light", "type": "area", "source": "built_in"},
                    {"name": "rim_point_light", "type": "point", "source": "built_in"},
                ],
                "camera": {"name": "camera_overview", "lens_mm": 35, "target": "center_cube"},
            },
            "script_policy": {
                "arbitrary_python": "disabled",
                "private_blend": "not_opened",
                "external_assets": "not_loaded",
                "textures_hdri_addons": "not_used",
            },
            "write_policy": {
                "dry_run_default": True,
                "real_render_requires": [
                    "confirmed local Blender run",
                    "ignored output directory",
                    "reviewed manifest",
                ],
            },
            "next_steps": [
                "Review this plan before adding any Blender CLI render path.",
                "If a render is later enabled, keep the script fixed-template and output under examples/output or output.",
            ],
        }
    )
