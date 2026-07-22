from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from benchmark.vector60.aggregate import (
    SummaryValidationError,
    aggregate_summary,
    main,
    render_markdown,
    validate_summary,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def make_summary() -> dict[str, object]:
    cases: list[dict[str, object]] = []
    for category in ("logo_or_icon", "lineart", "flat", "illustration"):
        for index in range(1, 11):
            cases.append(
                {
                    "case_id": f"{category}-{index:02d}",
                    "category": category,
                    "status": "passed",
                    "metrics": {
                        "edge_dice": 0.94,
                        "artisan_baseline_edge_dice": 0.90,
                        "normalized_mae": 0.05,
                        "seam_free_4x": True,
                        "anchor_count": 70,
                        "artisan_baseline_anchor_count": 100,
                        "safe_svg": {
                            "no_bitmap": True,
                            "no_script": True,
                            "no_external_links": True,
                        },
                    },
                }
            )
    return {
        "schema_version": "vector60-summary-v1",
        "cases": cases,
        "exact_validation": {
            "pixel_match": True,
            "different_pixel_count": 0,
            "maximum_channel_difference": 0,
        },
        "test_suites": {"python": "passed", "frontend": "passed", "rust": "passed"},
    }


class Vector60BenchmarkTests(unittest.TestCase):
    def test_all_hard_gates_pass_only_with_complete_evidence(self) -> None:
        result = aggregate_summary(make_summary())

        self.assertEqual(result["overall_status"], "passed")
        self.assertEqual(result["case_counts"]["passed"], 40)
        self.assertEqual(result["gate_counts"], {"passed": 8, "failed": 0, "unverified": 0})
        self.assertTrue(all(gate["status"] == "passed" for gate in result["gates"].values()))

    def test_missing_evidence_is_unverified_and_never_defaults_to_passed(self) -> None:
        summary = make_summary()
        first_case = summary["cases"][0]
        del first_case["metrics"]["edge_dice"]
        del summary["exact_validation"]
        summary["test_suites"]["rust"] = "skipped"

        result = aggregate_summary(summary)

        self.assertEqual(result["overall_status"], "unverified")
        self.assertEqual(result["gates"]["edge_dice_median"]["status"], "unverified")
        self.assertEqual(result["gates"]["exact_pixel_validation"]["status"], "unverified")
        self.assertEqual(result["gates"]["test_suites"]["status"], "unverified")

    def test_known_failures_fail_success_safety_exact_and_test_gates(self) -> None:
        summary = make_summary()
        for case in summary["cases"][:3]:
            case["status"] = "failed"
        summary["cases"][3]["metrics"]["safe_svg"]["no_script"] = False
        summary["exact_validation"]["different_pixel_count"] = 1
        summary["test_suites"]["frontend"] = "failed"

        result = aggregate_summary(summary)

        self.assertEqual(result["overall_status"], "failed")
        self.assertEqual(result["gates"]["success_count"]["status"], "failed")
        self.assertEqual(result["gates"]["safe_svg"]["status"], "failed")
        self.assertEqual(result["gates"]["exact_pixel_validation"]["status"], "failed")
        self.assertEqual(result["gates"]["test_suites"]["status"], "failed")

    def test_anchor_alternative_uses_paired_significance_evidence(self) -> None:
        summary = make_summary()
        for case in summary["cases"]:
            case["metrics"]["anchor_count"] = 105
            case["metrics"]["artisan_baseline_anchor_count"] = 100
            case["metrics"]["edge_dice"] = 0.92
            case["metrics"]["artisan_baseline_edge_dice"] = 0.88

        result = aggregate_summary(summary)
        anchor_gate = result["gates"]["anchor_rule"]

        self.assertEqual(anchor_gate["status"], "passed")
        self.assertAlmostEqual(anchor_gate["observed"]["ratio"], 1.05)
        self.assertLess(anchor_gate["observed"]["one_sided_sign_test_pvalue"], 0.05)

    def test_zero_anchor_baseline_does_not_claim_a_25_percent_reduction(self) -> None:
        summary = make_summary()
        for case in summary["cases"]:
            case["metrics"]["anchor_count"] = 0
            case["metrics"]["artisan_baseline_anchor_count"] = 0
            case["metrics"]["edge_dice"] = 0.90
            case["metrics"]["artisan_baseline_edge_dice"] = 0.90

        anchor_gate = aggregate_summary(summary)["gates"]["anchor_rule"]

        self.assertEqual(anchor_gate["status"], "failed")
        self.assertEqual(anchor_gate["observed"]["ratio"], 1.0)

    def test_incomplete_svg_safety_evidence_is_unverified_but_known_unsafe_fails(self) -> None:
        summary = make_summary()
        summary["cases"][0]["metrics"]["safe_svg"] = {}
        self.assertEqual(aggregate_summary(summary)["gates"]["safe_svg"]["status"], "unverified")

        summary["cases"][1]["metrics"]["safe_svg"]["no_bitmap"] = False
        self.assertEqual(aggregate_summary(summary)["gates"]["safe_svg"]["status"], "failed")

    def test_schema_rejects_nonanonymous_ids_extra_fields_and_bad_category_counts(self) -> None:
        private_id = make_summary()
        private_id["cases"][0]["case_id"] = "customer-logo.png"
        with self.assertRaisesRegex(
            SummaryValidationError, "case_id_must_be_anonymous_vector60_id"
        ):
            validate_summary(private_id)

        secret = make_summary()
        secret["cases"][0]["source_path"] = "private"
        with self.assertRaisesRegex(SummaryValidationError, "unknown_or_sensitive_field"):
            validate_summary(secret)

        duplicate = make_summary()
        duplicate["cases"][0]["case_id"] = duplicate["cases"][1]["case_id"]
        with self.assertRaisesRegex(SummaryValidationError, "duplicate_case_id"):
            validate_summary(duplicate)

    def test_markdown_contains_only_safe_relative_comparison_placeholders(self) -> None:
        report = render_markdown(aggregate_summary(make_summary()))

        self.assertIn("comparisons/logo_or_icon/logo_or_icon-01.png", report)
        self.assertIn("不代表对应图片已生成或已验证", report)
        self.assertNotIn("data:image", report)
        self.assertNotIn("http://", report)
        self.assertNotIn("https://", report)

    def test_cli_does_not_echo_private_input_path_on_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            private_name = "private-customer-material.json"
            input_path = Path(temporary_dir) / private_name
            input_path.write_text("not-json", encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = main(["--input", str(input_path)])

        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(
            stderr.getvalue(), '{"ok":false,"error":"invalid_or_unreadable_summary"}\n'
        )
        self.assertNotIn(private_name, stderr.getvalue())

    def test_initial_report_explicitly_remains_unverified(self) -> None:
        report = (REPO_ROOT / "benchmark" / "vector60" / "report.md").read_text(encoding="utf-8")

        self.assertIn("总状态：`unverified`", report)
        self.assertIn("尚未运行", report)
        self.assertIn("未验证：40", report)
        self.assertNotIn("总状态：`passed`", report)
        json.dumps(make_summary())


if __name__ == "__main__":
    unittest.main()
