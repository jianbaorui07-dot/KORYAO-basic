from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


for parent in Path(__file__).resolve().parents:
    if (parent / "starbridge_mcp").is_dir():
        sys.path.insert(0, str(parent))
        break

from starbridge_mcp.bridges.blender_safe_scene import build_reference_reconstruction_plan


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a dry-run Blender reference reconstruction plan."
    )
    parser.add_argument("--reference-name", default="reference_image")
    parser.add_argument("--target-kind", default="object_or_scene")
    parser.add_argument("--reference-views", type=int, default=1)
    parser.add_argument("--known-scale", default="")
    parser.add_argument("--tolerance-pixels", type=int, default=4)
    parser.add_argument("--max-iterations", type=int, default=8)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    plan = build_reference_reconstruction_plan(
        reference_name=args.reference_name,
        target_kind=args.target_kind,
        reference_views=args.reference_views,
        known_scale=args.known_scale,
        tolerance_pixels=args.tolerance_pixels,
        max_iterations=args.max_iterations,
    )
    if args.json:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return

    print("Blender reference reconstruction dry-run plan")
    print("reference:", plan["target"]["reference_name"])
    print("grade:", plan["target"]["reconstruction_grade"])
    print("mode:", plan["mode"])
    print("handoff:", plan["pipeline"][-1]["handoff_rule"])


if __name__ == "__main__":
    main()
