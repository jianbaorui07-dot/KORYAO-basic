from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


for parent in Path(__file__).resolve().parents:
    if (parent / "starbridge_mcp").is_dir():
        sys.path.insert(0, str(parent))
        break

from starbridge_mcp.bridges.blender_safe_scene import build_scene_plan


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a public-safe Blender scene dry-run plan.")
    parser.add_argument("--scene-name", default="starbridge_public_scene")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    plan = build_scene_plan(scene_name=args.scene_name, render_width=args.width, render_height=args.height)
    if args.json:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return
    print("Blender safe scene dry-run plan")
    print("scene:", plan["scene"]["name"])
    print("objects:", ", ".join(item["name"] for item in plan["scene"]["objects"]))
    print("mode:", plan["mode"])


if __name__ == "__main__":
    main()
