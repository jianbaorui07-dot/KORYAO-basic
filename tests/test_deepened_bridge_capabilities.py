from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from starbridge_mcp.bridges.blender_safe_scene import build_scene_plan
from starbridge_mcp.bridges.capcut_draft_structure import draft_structure_summary
from starbridge_mcp.bridges.illustrator_preflight import preflight_summary

BANNED_OUTPUT_FRAGMENTS = ("C:\\Users\\", "/Users/", "/home/", "Desktop", "Documents", "AppData")


class DeepenedBridgeCapabilitiesTest(unittest.TestCase):
    def assert_no_private_paths(self, payload: object) -> None:
        text = json.dumps(payload, ensure_ascii=False)
        for fragment in BANNED_OUTPUT_FRAGMENTS:
            self.assertNotIn(fragment, text)

    def test_blender_scene_plan_is_fixed_template_dry_run(self) -> None:
        plan = build_scene_plan(scene_name="demo", render_width=800, render_height=600)

        self.assertTrue(plan["ok"])
        self.assertEqual("dry_run", plan["mode"])
        self.assertEqual("disabled", plan["script_policy"]["arbitrary_python"])
        self.assertEqual("not_opened", plan["script_policy"]["private_blend"])
        self.assertGreaterEqual(len(plan["scene"]["objects"]), 3)
        self.assert_no_private_paths(plan)

    def test_illustrator_preflight_uses_sanitized_summary_only(self) -> None:
        result = preflight_summary(
            {
                "artboards": 1,
                "linked_assets": 2,
                "missing_links": 0,
                "text_objects": 3,
                "color_mode": "RGB",
            }
        )

        self.assertTrue(result["ok"])
        self.assertEqual("metadata_only", result["mode"])
        self.assertFalse(result["safety_policy"]["opens_ai_file"])
        self.assertFalse(result["safety_policy"]["exports_assets"])
        self.assert_no_private_paths(result)

    def test_capcut_draft_structure_does_not_read_draft_json_or_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "private_project_name").mkdir()
            (root / "draft_content.json").write_text('{"secret": "do not read"}', encoding="utf-8")
            with patch.dict(os.environ, {"CAPCUT_DRAFTS_DIR": str(root)}, clear=False):
                result = draft_structure_summary(max_entries=10)

        text = json.dumps(result, ensure_ascii=False)
        self.assertTrue(result["ok"])
        self.assertEqual(
            ["<SENSITIVE_DRAFT_FILE>"], result["roots"][0]["sensitive_marker_names_detected"]
        )
        self.assertNotIn("draft_content.json", text)
        self.assertNotIn("private_project_name", text)
        self.assertNotIn("do not read", text)
        self.assertFalse(result["safety_policy"]["draft_json_read"])
        self.assert_no_private_paths(result)


if __name__ == "__main__":
    unittest.main()
