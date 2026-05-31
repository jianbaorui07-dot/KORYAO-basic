from __future__ import annotations

import unittest

from examples.comfy_bridge.workflow_agent import workflow_build, workflow_build_plan


class ComfyWorkflowBuilderTests(unittest.TestCase):
    def test_goal_generates_workflow_build_plan(self) -> None:
        result = workflow_build_plan(
            {
                "goal": "生成一张国风 Q版 明代街市人物场景图",
                "workflow_type": "txt2img",
                "style": "Q版3D半动漫国风",
                "width": 1344,
                "height": 768,
            }
        )

        self.assertTrue(result["ok"])
        self.assertEqual("dry_run", result["mode"])
        self.assertEqual("txt2img", result["workflow_type"])
        self.assertIn("KSampler", result["required_nodes"])
        self.assertFalse(result["will_build"])

    def test_workflow_build_outputs_valid_json_hash_and_summary(self) -> None:
        result = workflow_build(
            {
                "goal": "生成一张国风 Q版 明代街市人物场景图",
                "style": "Q版3D半动漫国风",
                "width": 1344,
                "height": 768,
                "checkpoint": "model-placeholder.safetensors",
            }
        )

        self.assertTrue(result["ok"])
        self.assertEqual("dry_run", result["mode"])
        self.assertEqual(64, len(result["workflow_hash"]))
        self.assertIn("workflow", result)
        self.assertTrue(result["validation"]["ok"])
        self.assertEqual(7, result["node_summary"]["node_count"])
        self.assertEqual("CheckpointLoaderSimple", result["workflow"]["4"]["class_type"])
        self.assertEqual(1344, result["workflow"]["5"]["inputs"]["width"])
        self.assertEqual(768, result["workflow"]["5"]["inputs"]["height"])


if __name__ == "__main__":
    unittest.main()
