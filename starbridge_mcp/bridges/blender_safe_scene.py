from __future__ import annotations

from typing import Any

from starbridge_mcp.core.security import sanitize


def _clamp_int(value: int, *, minimum: int, maximum: int) -> int:
    return max(minimum, min(int(value), maximum))


def _clean_text(value: str, fallback: str) -> str:
    cleaned = str(value or "").strip()
    return cleaned or fallback


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


def build_reference_reconstruction_plan(
    *,
    reference_name: str = "reference_image",
    target_kind: str = "object_or_scene",
    reference_views: int = 1,
    known_scale: str = "",
    tolerance_pixels: int = 4,
    max_iterations: int = 8,
) -> dict[str, Any]:
    """Return a safe dry-run plan for reference-verified Blender reconstruction.

    This does not read images, launch Blender, run user Python, or claim that true
    hidden geometry can be recovered from a single view. It defines the gates a
    future local pipeline must pass before a reconstructed model can be handed off.
    """

    views = _clamp_int(reference_views, minimum=1, maximum=64)
    tolerance = _clamp_int(tolerance_pixels, minimum=1, maximum=64)
    iterations = _clamp_int(max_iterations, minimum=1, maximum=50)
    scale_anchor = _clean_text(known_scale, "missing_known_scale_anchor")

    if views == 1 and scale_anchor == "missing_known_scale_anchor":
        reconstruction_grade = "reference_view_match_only"
    elif views == 1:
        reconstruction_grade = "single_view_metric_approximation"
    else:
        reconstruction_grade = "multi_view_geometry_constrained"

    return sanitize(
        {
            "ok": True,
            "bridge": "blender",
            "action": "reference_reconstruction_plan",
            "mode": "dry_run",
            "maturity": "plan_only",
            "target": {
                "reference_name": _clean_text(reference_name, "reference_image"),
                "target_kind": _clean_text(target_kind, "object_or_scene"),
                "reference_views": views,
                "known_scale": scale_anchor,
                "reconstruction_grade": reconstruction_grade,
            },
            "pipeline": [
                {
                    "stage": "input_gate",
                    "purpose": "Accept only user-provided references and redacted metadata.",
                    "outputs": [
                        "reference_manifest",
                        "declared_view_count",
                        "known_scale_anchor_or_missing",
                    ],
                    "refusal_conditions": [
                        "no_reference_image",
                        "unlicensed_or_sensitive_source_asset",
                        "request_to_guess_hidden_geometry_as_fact",
                    ],
                },
                {
                    "stage": "visual_decomposition",
                    "purpose": "Extract masks, edges, regions, and named parts before modeling.",
                    "candidate_tools": [
                        "Photoshop object/subject masks",
                        "SAM2",
                        "GroundingDINO",
                        "OpenCV edges and contours",
                    ],
                    "outputs": [
                        "silhouette_mask",
                        "material_region_masks",
                        "part_labels",
                        "dominant_edges",
                    ],
                },
                {
                    "stage": "geometry_initialization",
                    "purpose": "Create geometry from visual constraints before any stylistic completion.",
                    "candidate_tools": [
                        "VGGT",
                        "Depth Anything 3",
                        "MapAnything",
                        "vggt-blender",
                        "DA3-blender",
                    ],
                    "outputs": [
                        "camera_guess",
                        "depth_or_point_cloud",
                        "coarse_mesh_or_blockout",
                    ],
                },
                {
                    "stage": "single_view_metrology",
                    "purpose": "Recover relative dimensions from perspective lines and scale anchors.",
                    "required_for_metric_scale": [
                        "known_real_world_measurement",
                        "vanishing_points_or_parallel_edges",
                        "camera_intrinsic_or_lens_guess",
                    ],
                    "outputs": [
                        "camera_projection",
                        "relative_width_height_depth_ratios",
                        "uncertain_thickness_flags",
                    ],
                },
                {
                    "stage": "blender_rebuild",
                    "purpose": "Build a semantic scene graph instead of free-form hallucinated geometry.",
                    "blender_plan_units": [
                        "scene_graph",
                        "camera",
                        "constrained_meshes",
                        "modifier_stack",
                        "material_slots_from_masks",
                    ],
                    "policy": "fixed templates and audited scripts only; no arbitrary Python execution.",
                },
                {
                    "stage": "render_compare_iterate",
                    "purpose": "Render from the recovered camera and compare against the reference.",
                    "max_iterations": iterations,
                    "comparison_metrics": {
                        "silhouette_iou_min": 0.97,
                        "edge_chamfer_px_max": tolerance,
                        "camera_reprojection_px_max": tolerance,
                        "visible_part_coverage_min": 0.95,
                        "material_region_iou_min": 0.90,
                    },
                    "outputs": [
                        "per_iteration_error_report",
                        "annotated_difference_overlay",
                        "accepted_or_needs_user_status",
                    ],
                },
                {
                    "stage": "handoff_gate",
                    "purpose": "Only hand off when visible-view evidence passes thresholds.",
                    "requires": [
                        "same-camera_render",
                        "mask_edge_metric_report",
                        "declared_unrecoverable_regions",
                        "reviewed_output_manifest",
                    ],
                    "handoff_rule": "Do not present the model as final if the reference-view metrics fail.",
                },
            ],
            "non_hallucination_contract": {
                "must_not_infer_as_fact": [
                    "hidden_back_side",
                    "occluded_interior",
                    "true_material_thickness_without_scale_or_side_view",
                    "absolute_dimensions_without_known_scale",
                ],
                "must_label_as_assumption": [
                    "back_side_completion",
                    "symmetry_guess",
                    "procedural_material_substitution",
                    "asset_library_replacement",
                ],
                "deliverable_claim_limit": (
                    "single-view output can be reference-view verified; true 3D accuracy needs "
                    "multi-view references or physical measurements"
                ),
            },
            "script_policy": {
                "arbitrary_python": "disabled",
                "private_blend": "not_opened",
                "reference_pixels": "not_read_by_this_plan",
                "external_model_downloads": "disabled",
                "generative_completion": "allowed_only_as_labeled_assumption",
            },
            "write_policy": {
                "dry_run_default": True,
                "real_run_requires": [
                    "explicit local confirmation",
                    "ignored output directory",
                    "redacted evidence manifest",
                    "same-camera comparison report",
                ],
            },
            "next_steps": [
                "Attach a user-provided reference image in a local-only run.",
                "Generate masks and camera/depth estimates before modeling.",
                "Render the Blender scene from the recovered camera and compare metrics.",
                "Ask for more views or a scale anchor when the hidden geometry is ambiguous.",
            ],
        }
    )
