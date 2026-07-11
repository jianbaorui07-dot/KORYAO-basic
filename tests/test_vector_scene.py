from __future__ import annotations

import unittest

from starbridge_mcp.core.vector_scene import (
    compile_vector_scene_to_svg,
    validate_vector_scene,
    vector_scene_summary,
)


def sample_scene() -> dict:
    return {
        "schema_version": "starbridge.vector-scene.v1",
        "scene_id": "scene.public_fixture",
        "document": {
            "width": 320,
            "height": 240,
            "units": "px",
            "color_mode": "RGB",
            "background": "#FFFFFF",
        },
        "palette": {"primary": "#2255AA", "ink": "#111111"},
        "layers": [
            {"id": "artwork", "name": "Artwork", "visible": True, "locked": False},
            {"id": "labels", "name": "Labels", "visible": True, "locked": False},
        ],
        "objects": [
            {
                "id": "shape.main",
                "layer_id": "artwork",
                "type": "path",
                "style": {
                    "fill": "@primary",
                    "stroke": "@ink",
                    "stroke_width": 2,
                    "opacity": 1,
                    "line_join": "round",
                },
                "commands": [
                    {"op": "M", "x": 30, "y": 30},
                    {"op": "L", "x": 180, "y": 30},
                    {"op": "C", "x1": 220, "y1": 30, "x2": 220, "y2": 160, "x": 180, "y": 180},
                    {"op": "L", "x": 30, "y": 180},
                    {"op": "Z"},
                ],
            },
            {
                "id": "label.main",
                "layer_id": "labels",
                "type": "text",
                "style": {
                    "fill": "@ink",
                    "stroke": None,
                    "stroke_width": 0,
                    "opacity": 1,
                },
                "x": 160,
                "y": 220,
                "text": "A&B <editable>",
                "font_family": "sans-serif",
                "font_size": 18,
                "text_anchor": "middle",
            },
        ],
    }


class VectorSceneTests(unittest.TestCase):
    def test_valid_scene_compiles_to_deterministic_svg_in_memory(self) -> None:
        scene = sample_scene()
        first = compile_vector_scene_to_svg(scene)
        second = compile_vector_scene_to_svg(scene)

        self.assertEqual([], validate_vector_scene(scene))
        self.assertEqual(first, second)
        self.assertIn('<g id="artwork"', first)
        self.assertIn('fill="#2255AA"', first)
        self.assertIn("M 30 30 L 180 30 C 220 30 220 160 180 180 L 30 180 Z", first)
        self.assertIn("A&amp;B &lt;editable&gt;", first)
        self.assertNotIn("<image", first)
        self.assertNotIn("<script", first)

    def test_scene_summary_is_sanitized_and_never_writes_files(self) -> None:
        summary = vector_scene_summary(sample_scene())

        self.assertTrue(summary["ok"])
        self.assertEqual(2, summary["layer_count"])
        self.assertEqual(2, summary["object_count"])
        self.assertFalse(summary["writes_files"])

    def test_duplicate_object_ids_are_rejected(self) -> None:
        scene = sample_scene()
        scene["objects"].append(dict(scene["objects"][0]))

        self.assertIn("object ids must be unique", validate_vector_scene(scene))
        with self.assertRaisesRegex(ValueError, "object ids must be unique"):
            compile_vector_scene_to_svg(scene)

    def test_unknown_layer_is_rejected(self) -> None:
        scene = sample_scene()
        scene["objects"][0]["layer_id"] = "private_layer"

        self.assertTrue(validate_vector_scene(scene))

    def test_path_must_start_with_move(self) -> None:
        scene = sample_scene()
        scene["objects"][0]["commands"][0] = {"op": "L", "x": 30, "y": 30}

        self.assertIn("path must start with M", validate_vector_scene(scene))

    def test_raw_svg_or_script_fields_are_rejected(self) -> None:
        scene = sample_scene()
        scene["objects"][0]["raw_svg"] = '<script>alert("x")</script>'

        failures = validate_vector_scene(scene)
        self.assertTrue(any("unsupported fields" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()
