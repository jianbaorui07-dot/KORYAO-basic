from __future__ import annotations

import unittest

from starbridge_mcp.core.vector_intent import parse_vector_command, validate_vector_task


class VectorIntentTests(unittest.TestCase):
    def test_minimal_command_expands_to_safe_production_defaults(self) -> None:
        result = parse_vector_command("照图重绘")
        task = result["task"]

        self.assertTrue(result["ok"])
        self.assertEqual("reference_vector_rebuild", task["task"])
        self.assertEqual("semantic_reconstruction", task["strategy"])
        self.assertTrue(task["dry_run"])
        self.assertFalse(task["confirm_write"])
        self.assertFalse(task["structure"]["image_trace"])
        self.assertEqual(2, task["review"]["max_repair_rounds"])
        self.assertEqual([], validate_vector_task(task))

    def test_detailed_short_command_extracts_numeric_and_export_constraints(self) -> None:
        result = parse_vector_command(
            "照图重绘｜语义重建｜分层+少节点+文字可编｜限5色+无渐变｜轮廓负形必准｜五维95分+修3轮｜SVG+PDF"
        )
        task = result["task"]

        self.assertEqual(5, task["style"]["max_colors"])
        self.assertFalse(task["style"]["gradient_allowed"])
        self.assertTrue(task["quality"]["negative_space_hard_gate"])
        self.assertEqual(95, task["quality"]["overall_min"])
        self.assertEqual(3, task["review"]["max_repair_rounds"])
        self.assertEqual(["svg", "pdf"], task["exports"])
        self.assertEqual([], task["unrecognized_terms"])
        self.assertEqual([], validate_vector_task(task))

    def test_conflicting_constraints_return_structured_error(self) -> None:
        result = parse_vector_command("照图重绘｜不用描摹+允许描摹")

        self.assertFalse(result["ok"])
        self.assertIsNone(result["task"])
        self.assertEqual([["不用描摹", "允许描摹"]], result["conflicts"])

    def test_unknown_language_is_retained_without_becoming_an_action(self) -> None:
        result = parse_vector_command("照图重绘｜使用未知神奇滤镜")

        self.assertTrue(result["ok"])
        self.assertEqual(["使用未知神奇滤镜"], result["task"]["unrecognized_terms"])
        self.assertTrue(result["task"]["dry_run"])

    def test_empty_command_is_rejected(self) -> None:
        result = parse_vector_command("   ")
        self.assertFalse(result["ok"])


if __name__ == "__main__":
    unittest.main()
