from __future__ import annotations

import unittest

import numpy as np
from PIL import Image, ImageDraw

from starbridge_mcp.vectorization.vector60.preprocess import (
    preprocess_for_scene,
    preprocess_image,
)
from starbridge_mcp.vectorization.vector60.scene_classifier import (
    SUPPORTED_SCENES,
    classify_scene,
    extract_scene_features,
    validate_scene,
)


class Vector60SceneClassifierTests(unittest.TestCase):
    def test_supported_scene_contract_has_exactly_five_values(self) -> None:
        self.assertEqual(
            SUPPORTED_SCENES,
            ("logo", "lineart", "flat", "illustration", "unsupported_photo"),
        )
        for scene in SUPPORTED_SCENES:
            self.assertEqual(validate_scene(scene), scene)
        with self.assertRaisesRegex(ValueError, "supported Vector60 presets"):
            validate_scene("photorealistic-pro")

    def test_logo_classification_is_deterministic_and_report_safe(self) -> None:
        image = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((20, 20, 108, 108), radius=18, fill=(32, 92, 180, 255))
        draw.ellipse((45, 45, 83, 83), fill=(255, 255, 255, 255))

        first = classify_scene(image)
        second = classify_scene(image.copy())

        self.assertEqual(first, second)
        self.assertEqual(first.scene, "logo")
        self.assertEqual(first.reasons, ("compact_palette", "large_uniform_regions"))
        self.assertEqual(set(first.as_dict()), {"scene", "confidence", "reasons", "features"})

    def test_lineart_flat_and_illustration_are_distinguished(self) -> None:
        lineart = Image.new("RGB", (160, 120), "white")
        draw = ImageDraw.Draw(lineart)
        draw.line((15, 100, 45, 20, 80, 90, 120, 25, 145, 100), fill="black", width=3)
        draw.ellipse((55, 35, 105, 85), outline="black", width=3)

        flat = Image.new("RGB", (160, 120), (245, 235, 210))
        draw = ImageDraw.Draw(flat)
        draw.rectangle((0, 75, 160, 120), fill=(48, 133, 96))
        draw.ellipse((20, 15, 95, 90), fill=(230, 91, 68))
        draw.polygon(((85, 95), (125, 25), (155, 95)), fill=(48, 91, 180))

        width, height = 160, 120
        x = np.linspace(0.0, 1.0, width, dtype=np.float32)[None, :]
        y = np.linspace(0.0, 1.0, height, dtype=np.float32)[:, None]
        illustration_array = np.empty((height, width, 3), dtype=np.uint8)
        illustration_array[..., 0] = np.round((0.55 + 0.4 * x) * 255).astype(np.uint8)
        illustration_array[..., 1] = np.round((0.25 + 0.6 * y) * 255).astype(np.uint8)
        illustration_array[..., 2] = np.round((0.8 - 0.4 * x * y) * 255).astype(np.uint8)
        illustration = Image.fromarray(illustration_array, "RGB")

        self.assertEqual(classify_scene(lineart).scene, "lineart")
        self.assertEqual(classify_scene(flat).scene, "flat")
        self.assertEqual(classify_scene(illustration).scene, "illustration")

    def test_photo_gate_requires_multiple_strong_signals(self) -> None:
        random = np.random.default_rng(20260722)
        base = random.integers(0, 256, size=(144, 192, 3), dtype=np.uint8)
        yy, xx = np.indices((144, 192))
        base[..., 0] = (base[..., 0] // 2 + (xx * 255 // 191) // 2).astype(np.uint8)
        base[..., 1] = (base[..., 1] // 2 + (yy * 255 // 143) // 2).astype(np.uint8)
        photo = Image.fromarray(base, "RGB")

        result = classify_scene(photo)

        self.assertEqual(result.scene, "unsupported_photo")
        self.assertIn("photo_gate_passed", result.reasons)
        self.assertGreaterEqual(result.confidence, 0.9)

    def test_features_are_aggregate_and_stable(self) -> None:
        image = Image.new("RGB", (8, 8), (20, 40, 60))
        features = extract_scene_features(image)
        payload = features.as_dict()
        self.assertEqual(payload["quantized_color_count"], 1)
        self.assertEqual(payload["edge_density"], 0.0)
        self.assertNotIn("path", payload)
        self.assertNotIn("pixels", payload)


class Vector60PreprocessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.image = Image.new("RGBA", (48, 36), (230, 220, 200, 255))
        draw = ImageDraw.Draw(self.image)
        draw.rectangle((5, 5, 25, 25), fill=(190, 50, 45, 128))
        draw.line((2, 32, 45, 3), fill=(20, 30, 40, 255), width=2)

    def test_each_scene_has_an_explicit_policy_and_preserves_input(self) -> None:
        original = self.image.tobytes()
        policies = {}
        for scene in SUPPORTED_SCENES:
            with self.subTest(scene=scene):
                result = preprocess_image(self.image, scene)
                policies[scene] = result.operations
                self.assertEqual(result.image.size, self.image.size)
                self.assertEqual(result.image.mode, "RGBA")
                self.assertEqual(result.scene, scene)
                self.assertEqual(
                    result.image.getchannel("A").tobytes(), self.image.getchannel("A").tobytes()
                )
                self.assertEqual(result.metadata()["width"], 48)
        self.assertEqual(self.image.tobytes(), original)
        self.assertEqual(len(set(policies.values())), len(SUPPORTED_SCENES))

    def test_unsupported_photo_is_identity_fallback_without_quality_claim(self) -> None:
        result = preprocess_for_scene(self.image, "unsupported_photo")

        self.assertIsNot(result.image, self.image)
        self.assertEqual(result.image.tobytes(), self.image.tobytes())
        self.assertFalse(result.enhancement_allowed)
        self.assertEqual(result.operations, ("identity_fallback",))

    def test_other_scenes_allow_only_in_memory_enhancement(self) -> None:
        for scene in ("logo", "lineart", "flat", "illustration"):
            with self.subTest(scene=scene):
                result = preprocess_for_scene(self.image, scene)
                self.assertTrue(result.enhancement_allowed)
                self.assertNotEqual(result.operations, ("identity_fallback",))
                self.assertEqual(
                    set(result.metadata()),
                    {"scene", "operations", "enhancement_allowed", "width", "height"},
                )


if __name__ == "__main__":
    unittest.main()
