from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_ROOT = REPO_ROOT / "examples" / "illustrator_bridge" / "protocols"


class VectorProtocolSchemaTests(unittest.TestCase):
    def load(self, name: str) -> dict:
        return json.loads((PROTOCOL_ROOT / name).read_text(encoding="utf-8"))

    def test_all_vector_protocol_schemas_are_valid_json_with_closed_root(self) -> None:
        names = (
            "vector_task.v1.schema.json",
            "vector_scene.v1.schema.json",
            "vector_patch.v1.schema.json",
            "reference_vector_quality.v1.schema.json",
        )
        for name in names:
            with self.subTest(name=name):
                schema = self.load(name)
                self.assertEqual("object", schema["type"])
                self.assertFalse(schema["additionalProperties"])
                self.assertTrue(schema["required"])

    def test_scene_schema_has_no_image_or_arbitrary_script_object(self) -> None:
        schema_text = json.dumps(self.load("vector_scene.v1.schema.json"))
        object_types = self.load("vector_scene.v1.schema.json")["$defs"]["object"]["properties"]["type"]["enum"]

        self.assertNotIn("image", object_types)
        self.assertNotIn("script", object_types)
        self.assertNotIn("execute", schema_text.lower())
        self.assertNotIn("url", schema_text.lower())

    def test_patch_schema_is_diff_only_and_targets_existing_ids(self) -> None:
        schema = self.load("vector_patch.v1.schema.json")
        operation = schema["properties"]["operations"]["items"]

        self.assertEqual("diff_only", schema["properties"]["mode"]["const"])
        self.assertIn("target_object_id", operation["required"])
        self.assertNotIn("add_object", operation["properties"]["operation"]["enum"])

    def test_task_schema_forces_safe_dry_run_defaults(self) -> None:
        schema = self.load("vector_task.v1.schema.json")

        self.assertTrue(schema["properties"]["dry_run"]["const"])
        self.assertFalse(schema["properties"]["confirm_write"]["const"])


if __name__ == "__main__":
    unittest.main()
