from __future__ import annotations

import json
import unittest
from pathlib import Path

from starbridge_mcp.core.vector_quality import (
    VectorDimensionResult,
    VectorQualityFinding,
    evaluate_reference_vector_quality,
    validate_reference_vector_quality_report,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = (
    REPO_ROOT
    / "examples"
    / "illustrator_bridge"
    / "protocols"
    / "reference_vector_quality.v1.schema.json"
)


def passing_dimensions() -> dict[str, VectorDimensionResult]:
    return {
        "geometry": VectorDimensionResult(94, ("silhouette", "alignment")),
        "topology": VectorDimensionResult(95, ("closed_paths", "negative_space")),
        "editability": VectorDimensionResult(90, ("anchor_budget", "live_text")),
        "visual": VectorDimensionResult(92, ("color", "composition")),
        "production": VectorDimensionResult(93, ("artboard", "export_profile")),
    }


def passing_gates() -> dict[str, bool]:
    return {
        "reference_authorized": True,
        "primary_silhouette_present": True,
        "topology_valid": True,
        "editable_vector_present": True,
        "safe_output_scope": True,
    }


class ReferenceVectorQualityTests(unittest.TestCase):
    def test_public_schema_declares_five_dimensions_and_safe_gates(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        dimension_properties = schema["properties"]["dimensions"]["properties"]
        gate_properties = schema["properties"]["hard_gates"]["properties"]

        self.assertEqual(
            {"geometry", "topology", "editability", "visual", "production"},
            set(dimension_properties),
        )
        self.assertIn("reference_authorized", gate_properties)
        self.assertIn("editable_vector_present", gate_properties)
        self.assertIn("safe_output_scope", gate_properties)

    def test_high_quality_editable_reconstruction_passes(self) -> None:
        report = evaluate_reference_vector_quality(
            reference_id="reference::public-fixture",
            candidate_id="candidate::sandbox-preview",
            dimensions=passing_dimensions(),
            hard_gates=passing_gates(),
        )

        self.assertEqual("pass", report["verdict"])
        self.assertGreaterEqual(report["overall_score"], 90)
        self.assertEqual([], validate_reference_vector_quality_report(report))

    def test_low_editability_requires_repair_even_when_visual_score_is_high(self) -> None:
        dimensions = passing_dimensions()
        dimensions["editability"] = VectorDimensionResult(
            60, ("too_many_anchor_points", "embedded_text")
        )
        report = evaluate_reference_vector_quality(
            reference_id="reference::public-fixture",
            candidate_id="candidate::sandbox-preview",
            dimensions=dimensions,
            hard_gates=passing_gates(),
        )

        self.assertEqual("repair_needed", report["verdict"])
        self.assertEqual(60, report["minimum_dimension_score"])

    def test_failed_topology_gate_blocks_delivery(self) -> None:
        gates = passing_gates()
        gates["topology_valid"] = False
        report = evaluate_reference_vector_quality(
            reference_id="reference::public-fixture",
            candidate_id="candidate::sandbox-preview",
            dimensions=passing_dimensions(),
            hard_gates=gates,
        )

        self.assertEqual("blocked", report["verdict"])

    def test_critical_finding_blocks_delivery_and_is_sanitized(self) -> None:
        report = evaluate_reference_vector_quality(
            reference_id="reference::public-fixture",
            candidate_id="candidate::sandbox-preview",
            dimensions=passing_dimensions(),
            hard_gates=passing_gates(),
            findings=[
                VectorQualityFinding(
                    code="embedded_reference_image",
                    dimension="editability",
                    severity="critical",
                    message="Candidate contains an embedded raster instead of editable vectors.",
                    object_id="object_12",
                    suggested_patch="replace_with_vector_paths",
                )
            ],
        )

        self.assertEqual("blocked", report["verdict"])
        self.assertNotIn("C:\\Users\\", json.dumps(report))


if __name__ == "__main__":
    unittest.main()
