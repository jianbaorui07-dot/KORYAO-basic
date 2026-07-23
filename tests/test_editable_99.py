from __future__ import annotations

import hashlib
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image, ImageDraw

from starbridge_mcp.backend import KORYAOBackend
from starbridge_mcp.vectorization import (
    RunConfig,
    VectorizationError,
    adaptive_optimize,
    cli,
    engine,
    run_vectorization,
)
from starbridge_mcp.vectorization.app_model import MODE_CARDS, parameters_for_mode
from starbridge_mcp.vectorization.presets import PRESETS


class Editable99PresetTests(unittest.TestCase):
    def test_editable_99_preset_exposes_the_acceptance_thresholds(self) -> None:
        self.assertIn("editable-99", adaptive_optimize.QUALITY_PRESETS)
        thresholds = adaptive_optimize.QUALITY_PRESETS["editable-99"]

        self.assertEqual(thresholds.minimum_ssim, 0.990)
        self.assertEqual(thresholds.maximum_difference_percent, 1.0)
        self.assertEqual(thresholds.maximum_normalized_mae, 0.010)
        self.assertEqual(thresholds.minimum_edge_dice, 0.980)
        self.assertEqual(thresholds.maximum_alpha_mae, 0.005)

    def test_editable_99_vector_preset_tracks_complexity_limits(self) -> None:
        self.assertIn("editable-99", PRESETS)
        preset = PRESETS["editable-99"]

        self.assertEqual(preset.colors, 256)
        self.assertEqual(preset.preferred_subpaths, 30_000)
        self.assertEqual(preset.warning_subpaths, 60_000)
        self.assertEqual(preset.preferred_points, 120_000)
        self.assertEqual(preset.warning_points, 240_000)

    def test_editable_99_accepts_a_one_percent_target_override(self) -> None:
        try:
            options, thresholds = adaptive_optimize.validated_options(
                adaptive_optimize.AdaptiveOptions(
                    quality_preset="editable-99",
                    target_difference=1.0,
                )
            )
        except adaptive_optimize.AdaptiveOptimizationError as exc:
            self.fail(f"editable-99 one-percent target was rejected: {exc.code}")

        self.assertEqual(options.quality_preset, "editable-99")
        self.assertEqual(thresholds.maximum_difference_percent, 1.0)

    def test_candidate_color_schedule_is_high_to_low_and_complete(self) -> None:
        schedule = adaptive_optimize.EDITABLE_99_COLOR_CANDIDATES

        self.assertEqual(schedule, (256, 192, 160, 128, 96, 80, 64, 48, 32))

    def test_cli_and_app_model_expose_editable_99_without_manual_color_override(self) -> None:
        try:
            parsed = cli.parse_args(
                [
                    "--input",
                    "placeholder.png",
                    "--mode",
                    "editable-99",
                    "--quality-preset",
                    "editable-99",
                    "--target-difference",
                    "1.0",
                ]
            )
        except Exception as exc:
            self.fail(f"editable-99 CLI arguments were rejected: {type(exc).__name__}")
        config = cli.config_from_args(parsed)
        parameters = parameters_for_mode("editable-99")

        self.assertEqual(config.mode, "editable-99")
        self.assertEqual(config.quality_preset, "editable-99")
        self.assertEqual(config.target_difference, 1.0)
        self.assertIsNone(parameters.colors)
        self.assertTrue(any(card.key == "editable-99" for card in MODE_CARDS))


class Editable99QualityGateTests(unittest.TestCase):
    def test_alpha_mae_is_a_required_quality_gate(self) -> None:
        quality_gates = adaptive_optimize.quality_gates
        thresholds = adaptive_optimize.QUALITY_PRESETS["editable-99"]
        metrics = {
            "ssim": 0.999,
            "difference_percent": 0.1,
            "normalized_mae": 0.001,
            "edge_dice": 0.999,
            "alpha_mae": 0.006,
        }
        evidence = {"embedded_raster_count": 0, "external_reference_count": 0}

        gates = quality_gates(metrics, evidence, thresholds)

        self.assertFalse(gates["alpha_mae"])
        self.assertFalse(all(gates.values()))

    def test_all_five_quality_metrics_must_pass(self) -> None:
        quality_gates = adaptive_optimize.quality_gates
        thresholds = adaptive_optimize.QUALITY_PRESETS["editable-99"]
        metrics = {
            "ssim": 0.990,
            "difference_percent": 1.0,
            "normalized_mae": 0.010,
            "edge_dice": 0.980,
            "alpha_mae": 0.005,
        }
        evidence = {"embedded_raster_count": 0, "external_reference_count": 0}

        gates = quality_gates(metrics, evidence, thresholds)

        self.assertTrue(all(gates.values()))


class Editable99SelectionTests(unittest.TestCase):
    @staticmethod
    def candidate(
        identifier: str,
        *,
        subpaths: int,
        points: int,
        colors: int,
        size: int,
        elapsed: float = 1.0,
    ) -> dict:
        return {
            "candidate_id": identifier,
            "status": "pass",
            "final_render_metrics": {
                "ssim": 0.995,
                "difference_percent": 0.5,
                "normalized_mae": 0.004,
                "edge_dice": 0.99,
                "alpha_mae": 0.001,
            },
            "vector": {
                "subpaths": subpaths,
                "anchors": points,
                "colors": colors,
                "bytes": size,
            },
            "elapsed_seconds": elapsed,
        }

    def test_selection_minimizes_subpaths_then_points_colors_and_size(self) -> None:
        select_candidate = adaptive_optimize.select_editable_99_candidate
        candidates = [
            self.candidate("few-points", subpaths=20, points=40, colors=32, size=900),
            self.candidate("few-subpaths", subpaths=19, points=200, colors=256, size=2_000),
            self.candidate("failed", subpaths=1, points=4, colors=2, size=100),
        ]
        candidates[-1]["status"] = "preview-only"

        selected = select_candidate(candidates)

        self.assertEqual(selected["candidate_id"], "few-subpaths")

    def test_ties_are_broken_by_points_then_colors_then_svg_size(self) -> None:
        select_candidate = adaptive_optimize.select_editable_99_candidate
        candidates = [
            self.candidate("large", subpaths=10, points=30, colors=64, size=800),
            self.candidate("few-colors", subpaths=10, points=30, colors=48, size=900),
            self.candidate("few-points", subpaths=10, points=29, colors=256, size=2_000),
        ]

        selected = select_candidate(candidates)

        self.assertEqual(selected["candidate_id"], "few-points")


class IllustratorSafetyTests(unittest.TestCase):
    def test_complexity_policy_allows_only_the_safe_range_to_auto_open(self) -> None:
        assess = adaptive_optimize.assess_illustrator_complexity
        preset = PRESETS["editable-99"]

        safe = assess(30_000, 120_000, preset)
        warning = assess(30_001, 120_001, preset)
        blocked = assess(60_001, 240_001, preset)
        archive = assess(300_001, 1_200_004, preset)

        self.assertEqual(safe["risk_level"], "safe")
        self.assertTrue(safe["auto_open_allowed"])
        self.assertEqual(warning["risk_level"], "warning")
        self.assertFalse(warning["auto_open_allowed"])
        self.assertEqual(blocked["risk_level"], "blocked")
        self.assertFalse(blocked["auto_open_allowed"])
        self.assertEqual(archive["risk_level"], "archive")
        self.assertFalse(archive["auto_open_allowed"])

    def test_result_status_distinguishes_quality_failure_warning_and_conflict(self) -> None:
        status = adaptive_optimize.derive_editable_99_status

        self.assertEqual(status(False, "safe"), "quality_not_met")
        self.assertEqual(status(True, "safe"), "passed_editable_99")
        self.assertEqual(status(True, "warning"), "passed_quality_high_complexity")
        self.assertEqual(status(True, "blocked"), "quality_and_editability_conflict")
        self.assertEqual(status(True, "archive"), "quality_and_editability_conflict")


class Editable99EngineIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_dir.name)
        self.output_root = self.root / "examples" / "output" / "vectorization"
        self.repo_patch = mock.patch.object(engine, "REPO_ROOT", self.root)
        self.output_patch = mock.patch.object(engine, "OUTPUT_ROOT", self.output_root)
        self.repo_patch.start()
        self.output_patch.start()

    def tearDown(self) -> None:
        self.output_patch.stop()
        self.repo_patch.stop()
        self.temporary_dir.cleanup()

    def test_flat_transparent_image_publishes_verified_editable_99_evidence(self) -> None:
        source = self.root / "private-customer-flat.png"
        image = Image.new("RGBA", (32, 24), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rectangle((2, 2, 15, 20), fill=(28, 98, 214, 255))
        draw.rectangle((16, 4, 29, 18), fill=(245, 174, 45, 128))
        image.save(source)
        original_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()

        result = run_vectorization(
            RunConfig(
                input_path=str(source),
                mode="editable-99",
                reference_id="editable-flat",
                resource_budget="high",
            )
        )

        self.assertIn("editable_99", result)
        editable = result["editable_99"]
        self.assertEqual(editable["status"], "passed_editable_99")
        self.assertGreaterEqual(editable["candidate_count"], 2)
        self.assertEqual(editable["thresholds"]["ssim"], 0.990)
        self.assertEqual(editable["thresholds"]["difference_percent"], 1.0)
        self.assertEqual(editable["thresholds"]["normalized_mae"], 0.010)
        self.assertEqual(editable["thresholds"]["edge_dice"], 0.980)
        self.assertEqual(editable["thresholds"]["alpha_mae"], 0.005)
        self.assertTrue(all(editable["quality_gates"].values()))
        self.assertTrue(editable["illustrator_safety"]["auto_open_allowed"])
        self.assertEqual(result["mode"]["key"], "editable-99")
        self.assertEqual(original_sha256, hashlib.sha256(source.read_bytes()).hexdigest())
        self.assertIn("source_integrity", result)
        self.assertEqual(
            result["source_integrity"],
            {
                "before_sha256": original_sha256,
                "after_sha256": original_sha256,
                "unchanged": True,
            },
        )
        self.assertFalse(result["validation"]["image_trace_used"])
        self.assertEqual(result["validation"]["embedded_raster_count"], 0)

        for candidate in editable["candidates"]:
            self.assertIn("requested_colors", candidate)
            self.assertIn("metrics", candidate)
            self.assertIn("vector", candidate)
            self.assertIn("elapsed_seconds", candidate)
            self.assertIn("rejection_reason", candidate)
            self.assertIn("alpha_mae", candidate["metrics"])

        output = self.output_root / "editable-flat" / "editable-99"
        self.assertTrue((output / "vector.svg").is_file())
        self.assertTrue((output / "svg_render.png").is_file())
        self.assertTrue((output / "error_heatmap.png").is_file())
        self.assertTrue((output / "editable_99.json").is_file())
        report_text = (output / "vector_report.json").read_text(encoding="utf-8")
        markdown_text = (output / "vector_report.md").read_text(encoding="utf-8")
        self.assertNotIn(str(source), report_text)
        self.assertNotIn(source.name, report_text)
        self.assertIn("SSIM：1.0000 / ≥ 0.9900", markdown_text)
        self.assertIn("Alpha MAE：0.0000 / ≤ 0.0050", markdown_text)
        self.assertIn("结果状态：`passed_editable_99`", markdown_text)
        self.assertIn("Illustrator 自动打开：允许", markdown_text)
        compact = cli.compact_result(result)
        self.assertIsInstance(compact["optimization"], dict)
        optimization = compact["optimization"]
        self.assertEqual(optimization["status"], "passed_editable_99")
        self.assertGreaterEqual(
            optimization["final_render_metrics"]["ssim"],
            0.990,
        )
        self.assertTrue(optimization["illustrator_safety"]["auto_open_allowed"])
        self.assertIn(
            "editable_99_report",
            {artifact["role"] for artifact in compact["artifacts"]},
        )

    def test_thin_color_candidate_failure_retains_the_verified_exact_baseline(self) -> None:
        source = self.root / "thin-stripes.png"
        image = Image.new("RGBA", (64, 64), (255, 255, 255, 255))
        draw = ImageDraw.Draw(image)
        for x in range(64):
            draw.line(
                (x, 0, x, 63),
                fill=((x * 47) % 256, (x * 83) % 256, (x * 131) % 256, 255),
            )
        image.save(source)

        try:
            result = run_vectorization(
                RunConfig(
                    input_path=str(source),
                    mode="editable-99",
                    reference_id="editable-thin-stripes",
                    resource_budget="high",
                )
            )
        except VectorizationError as exc:
            self.fail(f"color candidate failure escaped the optimizer: {exc.code}")

        editable = result["editable_99"]
        self.assertEqual(editable["status"], "passed_editable_99")
        self.assertEqual(editable["selected_candidate"], "exact-baseline")
        self.assertGreater(len(editable["generation_failures"]), 0)
        self.assertTrue(
            all(item["error_code"] == "no_vector_paths" for item in editable["generation_failures"])
        )

    def test_local_recovery_revalidates_hotspot_metrics_and_can_be_selected(self) -> None:
        source = self.root / "color-grid.png"
        image = Image.new("RGBA", (64, 64), (255, 255, 255, 255))
        draw = ImageDraw.Draw(image)
        for row in range(8):
            for column in range(8):
                index = row * 8 + column
                draw.rectangle(
                    (column * 8, row * 8, column * 8 + 7, row * 8 + 7),
                    fill=(
                        (index * 47) % 256,
                        (index * 83) % 256,
                        (index * 131) % 256,
                        255,
                    ),
                )
        image.save(source)

        result = run_vectorization(
            RunConfig(
                input_path=str(source),
                mode="editable-99",
                reference_id="editable-local-recovery",
                resource_budget="high",
            )
        )

        editable = result["editable_99"]
        recovery = editable["local_recovery"]
        self.assertTrue(recovery["attempted"])
        self.assertIn("selected", recovery)
        self.assertTrue(recovery["selected"])
        self.assertTrue(editable["selected_candidate"].startswith("local-recovery-"))
        self.assertGreater(len(recovery["actions"]), 0)
        action = recovery["actions"][-1]
        self.assertEqual(action["trigger"], "quality_gate_failed_in_error_hotspot")
        self.assertLess(
            action["after_metrics"]["difference_percent"],
            action["before_metrics"]["difference_percent"],
        )
        self.assertTrue(action["passed"])
        self.assertTrue(all(editable["quality_gates"].values()))

    def test_resource_limit_failure_uses_the_declared_editable_99_status_code(self) -> None:
        source = self.root / "resource-limit.png"
        Image.new("RGBA", (32, 32), (28, 98, 214, 255)).save(source)

        with mock.patch.object(adaptive_optimize, "available_memory_bytes", return_value=1):
            try:
                run_vectorization(
                    RunConfig(
                        input_path=str(source),
                        mode="editable-99",
                        reference_id="editable-resource-limit",
                        resource_budget="low",
                    )
                )
            except VectorizationError as exc:
                self.assertEqual(exc.code, "resource_limit_exceeded")
            except Exception as exc:
                self.fail(f"resource failure was not structured: {type(exc).__name__}")
            else:
                self.fail("resource limit unexpectedly passed")


class Editable99BackendIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_dir.cleanup)
        self.backend = KORYAOBackend(app_data_dir=self.temporary_dir.name)

    def test_backend_accepts_editable_99_and_returns_quality_and_safety_metrics(self) -> None:
        source = Path(self.temporary_dir.name) / "private-flat.png"
        image = Image.new("RGBA", (32, 24), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rectangle((2, 2, 15, 20), fill=(28, 98, 214, 255))
        draw.rectangle((16, 4, 29, 18), fill=(245, 174, 45, 128))
        image.save(source)
        selected = self.backend.route(
            "POST",
            "/api/vectorization/selections",
            json.dumps({"input_path": str(source)}).encode("utf-8"),
        )
        selection_id = selected.body["data"]["selectionId"]

        started = self.backend.route(
            "POST",
            "/api/vectorization/jobs",
            json.dumps(
                {
                    "selection_id": selection_id,
                    "mode": "editable-99",
                    "parameters": {},
                    "confirm_run": True,
                    "confirm_write": True,
                    "confirm_export": True,
                }
            ).encode("utf-8"),
        )

        self.assertEqual(202, started.status, started.body)
        job_id = started.body["data"]["jobId"]
        deadline = time.monotonic() + 10
        completed = started
        while time.monotonic() < deadline:
            completed = self.backend.route("GET", f"/api/vectorization/jobs/{job_id}")
            if completed.body["data"]["status"] in {"completed", "failed"}:
                break
            time.sleep(0.05)
        self.assertEqual("completed", completed.body["data"]["status"], completed.body)
        result = completed.body["data"]["result"]
        self.assertEqual(result["status"], "passed_editable_99")
        self.assertGreaterEqual(result["metrics"]["ssim"], 0.990)
        self.assertLessEqual(result["metrics"]["differencePercent"], 1.0)
        self.assertLessEqual(result["metrics"]["normalizedMae"], 0.010)
        self.assertGreaterEqual(result["metrics"]["edgeDice"], 0.980)
        self.assertLessEqual(result["metrics"]["alphaMae"], 0.005)
        self.assertTrue(result["illustratorSafety"]["autoOpenAllowed"])

        workflows = self.backend.route("GET", "/api/workflows")
        vector_workflow = next(
            item
            for item in workflows.body["data"]["workflows"]
            if item["workflowId"] == "vector-delivery-v1"
        )
        self.assertIn("editable-99", vector_workflow["drawingModes"])


if __name__ == "__main__":
    unittest.main()
