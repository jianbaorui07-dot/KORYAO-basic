from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path


PYTHON_ROOTS = []
if os.environ.get("WORLDFORGE_PROJECT_ROOT"):
    PYTHON_ROOTS.append(Path(os.environ["WORLDFORGE_PROJECT_ROOT"]) / "Content" / "Python")
PYTHON_ROOTS.append(Path(__file__).resolve().parents[2])
for python_root in PYTHON_ROOTS:
    if str(python_root) not in sys.path:
        sys.path.insert(0, str(python_root))

from worldforge.Core import scene_validator  # noqa: E402


def project_root() -> Path:
    env_root = os.environ.get("WORLDFORGE_PROJECT_ROOT")
    if env_root:
        return Path(env_root)
    return Path(__file__).resolve().parents[4]


class SceneValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = project_root()

    def test_wf0009_recipe_schema(self) -> None:
        recipe_path = self.root / "Content" / "Python" / "WorldForge" / "Recipes" / "WF0009_SnowTemple_R1.json"
        recipe = scene_validator.load_recipe(recipe_path)
        result = scene_validator.validate_recipe_schema(recipe)
        self.assertTrue(result["ok"], result)

    def test_wf0010_recipe_schema(self) -> None:
        recipe_path = self.root / "Content" / "Python" / "WorldForge" / "Recipes" / "WF0010_DNABonsaiWorkshop_R1.json"
        recipe = scene_validator.load_recipe(recipe_path)
        result = scene_validator.validate_recipe_schema(recipe)
        self.assertTrue(result["ok"], result)
        self.assertEqual(recipe["mode"], "DEFINITION_ONLY")

    def test_wf0009_map_receipt_and_preview_are_valid(self) -> None:
        recipe_path = self.root / "Content" / "Python" / "WorldForge" / "Recipes" / "WF0009_SnowTemple_R1.json"
        recipe = scene_validator.load_recipe(recipe_path)
        map_path = scene_validator.map_disk_path(self.root, recipe["map_asset_path"])
        self.assertTrue(map_path.exists(), map_path)
        receipt = self.root / "Saved" / "WorldForge" / "Receipts" / "WF0009_R1_test_validation.json"
        self.assertTrue(receipt.exists(), receipt)
        preview = recipe["preview_profile"]["target_path"]
        png = scene_validator.validate_png(preview, 1280, 720)
        self.assertTrue(png["exists"], png)
        self.assertEqual(png["width"], 1280, png)
        self.assertEqual(png["height"], 720, png)
        self.assertGreater(png["size"], 16 * 1024, png)
        if not png["ok"]:
            self.assertIn("png_appears_blank", png["issues"], png)


if __name__ == "__main__":
    unittest.main()
