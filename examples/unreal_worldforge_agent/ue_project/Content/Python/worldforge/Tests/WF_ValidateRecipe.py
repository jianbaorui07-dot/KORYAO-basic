"""Small command-line validator for WorldForge recipes.

This script is intentionally importable by UE Python and normal CPython.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


PYTHON_ROOTS = []
if os.environ.get("WORLDFORGE_PROJECT_ROOT"):
    PYTHON_ROOTS.append(Path(os.environ["WORLDFORGE_PROJECT_ROOT"]) / "Content" / "Python")
PYTHON_ROOTS.append(Path(__file__).resolve().parents[2])
for python_root in PYTHON_ROOTS:
    if str(python_root) not in sys.path:
        sys.path.insert(0, str(python_root))

from worldforge.Core import scene_validator  # noqa: E402


def main() -> int:
    recipe_path = Path(os.environ.get("WORLDFORGE_RECIPE_PATH", ""))
    if not recipe_path:
        print(json.dumps({"ok": False, "error": "WORLDFORGE_RECIPE_PATH not set"}))
        return 2
    recipe = scene_validator.load_recipe(recipe_path)
    result = scene_validator.validate_recipe_schema(recipe)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
