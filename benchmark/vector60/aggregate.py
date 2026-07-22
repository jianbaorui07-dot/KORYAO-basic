"""Aggregate privacy-safe, per-case Vector60 benchmark summaries.

This module deliberately accepts metrics and verification flags only. It does not
inspect source images, SVG artifacts, renderer output, credentials, or user paths.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "vector60-summary-v1"
CATEGORIES = ("logo_or_icon", "lineart", "flat", "illustration")
CASE_STATUSES = frozenset({"passed", "failed", "skipped", "unverified"})
SUITE_STATUSES = frozenset({"passed", "failed", "skipped", "unverified"})
EXPECTED_CASE_IDS = frozenset(
    f"{category}-{index:02d}" for category in CATEGORIES for index in range(1, 11)
)

_ROOT_KEYS = frozenset({"schema_version", "cases", "exact_validation", "test_suites"})
_CASE_KEYS = frozenset({"case_id", "category", "status", "metrics"})
_METRIC_KEYS = frozenset(
    {
        "edge_dice",
        "artisan_baseline_edge_dice",
        "normalized_mae",
        "seam_free_4x",
        "anchor_count",
        "artisan_baseline_anchor_count",
        "safe_svg",
    }
)
_SAFE_SVG_KEYS = frozenset({"no_bitmap", "no_script", "no_external_links"})
_EXACT_KEYS = frozenset({"pixel_match", "different_pixel_count", "maximum_channel_difference"})
_SUITE_KEYS = frozenset({"python", "frontend", "rust"})
_GATE_ORDER = (
    "success_count",
    "edge_dice_median",
    "normalized_mae_median",
    "seam_free_4x",
    "anchor_rule",
    "safe_svg",
    "exact_pixel_validation",
    "test_suites",
)
_COMPARISON_REF_RE = re.compile(r"\Acomparisons/[a-z_]+/[a-z0-9_-]+\.png\Z")


class SummaryValidationError(ValueError):
    """Raised for an invalid or non-redacted Vector60 summary."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _reject_unknown_keys(value: Mapping[str, Any], allowed: frozenset[str]) -> None:
    if not set(value).issubset(allowed):
        raise SummaryValidationError("unknown_or_sensitive_field")


def _require_mapping(value: Any, code: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SummaryValidationError(code)
    return value


def _finite_number(value: Any, *, minimum: float, maximum: float, code: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SummaryValidationError(code)
    result = float(value)
    if not math.isfinite(result) or not minimum <= result <= maximum:
        raise SummaryValidationError(code)
    return result


def _nonnegative_integer(value: Any, code: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise SummaryValidationError(code)
    return value


def _optional_bool(value: Any, code: str) -> bool:
    if not isinstance(value, bool):
        raise SummaryValidationError(code)
    return value


def validate_summary(document: Any) -> dict[str, Any]:
    """Validate and normalize a Vector60 aggregate input.

    Unknown fields are rejected so paths, credentials, account state, and material
    content cannot be carried through as incidental metadata.
    """

    root = _require_mapping(document, "summary_must_be_object")
    _reject_unknown_keys(root, _ROOT_KEYS)
    if root.get("schema_version") != SCHEMA_VERSION:
        raise SummaryValidationError("unsupported_schema_version")

    raw_cases = root.get("cases")
    if not isinstance(raw_cases, Sequence) or isinstance(raw_cases, (str, bytes)):
        raise SummaryValidationError("cases_must_be_array")
    if len(raw_cases) != 40:
        raise SummaryValidationError("expected_40_cases")

    cases: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    category_counts = dict.fromkeys(CATEGORIES, 0)
    for raw_case in raw_cases:
        case = _require_mapping(raw_case, "case_must_be_object")
        _reject_unknown_keys(case, _CASE_KEYS)
        case_id = case.get("case_id")
        category = case.get("category")
        status = case.get("status")
        if case_id not in EXPECTED_CASE_IDS:
            raise SummaryValidationError("case_id_must_be_anonymous_vector60_id")
        if case_id in seen_ids:
            raise SummaryValidationError("duplicate_case_id")
        if category not in CATEGORIES or not case_id.startswith(f"{category}-"):
            raise SummaryValidationError("case_category_mismatch")
        if status not in CASE_STATUSES:
            raise SummaryValidationError("invalid_case_status")
        seen_ids.add(case_id)
        category_counts[category] += 1

        normalized: dict[str, Any] = {
            "case_id": case_id,
            "category": category,
            "status": status,
        }
        if "metrics" in case:
            metrics = _require_mapping(case["metrics"], "metrics_must_be_object")
            _reject_unknown_keys(metrics, _METRIC_KEYS)
            clean_metrics: dict[str, Any] = {}
            if "edge_dice" in metrics:
                clean_metrics["edge_dice"] = _finite_number(
                    metrics["edge_dice"], minimum=0.0, maximum=1.0, code="invalid_edge_dice"
                )
            if "artisan_baseline_edge_dice" in metrics:
                clean_metrics["artisan_baseline_edge_dice"] = _finite_number(
                    metrics["artisan_baseline_edge_dice"],
                    minimum=0.0,
                    maximum=1.0,
                    code="invalid_baseline_edge_dice",
                )
            if "normalized_mae" in metrics:
                clean_metrics["normalized_mae"] = _finite_number(
                    metrics["normalized_mae"],
                    minimum=0.0,
                    maximum=1.0,
                    code="invalid_normalized_mae",
                )
            if "seam_free_4x" in metrics:
                clean_metrics["seam_free_4x"] = _optional_bool(
                    metrics["seam_free_4x"], "invalid_seam_free_4x"
                )
            if "anchor_count" in metrics:
                clean_metrics["anchor_count"] = _nonnegative_integer(
                    metrics["anchor_count"], "invalid_anchor_count"
                )
            if "artisan_baseline_anchor_count" in metrics:
                clean_metrics["artisan_baseline_anchor_count"] = _nonnegative_integer(
                    metrics["artisan_baseline_anchor_count"],
                    "invalid_baseline_anchor_count",
                )
            if "safe_svg" in metrics:
                safe_svg = _require_mapping(metrics["safe_svg"], "safe_svg_must_be_object")
                _reject_unknown_keys(safe_svg, _SAFE_SVG_KEYS)
                clean_metrics["safe_svg"] = {
                    key: _optional_bool(safe_svg[key], f"invalid_{key}")
                    for key in _SAFE_SVG_KEYS
                    if key in safe_svg
                }
            normalized["metrics"] = clean_metrics
        cases.append(normalized)

    if seen_ids != EXPECTED_CASE_IDS or any(count != 10 for count in category_counts.values()):
        raise SummaryValidationError("expected_10_cases_per_category")

    normalized_root: dict[str, Any] = {"schema_version": SCHEMA_VERSION, "cases": cases}
    if "exact_validation" in root:
        exact = _require_mapping(root["exact_validation"], "exact_validation_must_be_object")
        _reject_unknown_keys(exact, _EXACT_KEYS)
        clean_exact: dict[str, Any] = {}
        if "pixel_match" in exact:
            clean_exact["pixel_match"] = _optional_bool(exact["pixel_match"], "invalid_pixel_match")
        if "different_pixel_count" in exact:
            clean_exact["different_pixel_count"] = _nonnegative_integer(
                exact["different_pixel_count"], "invalid_different_pixel_count"
            )
        if "maximum_channel_difference" in exact:
            clean_exact["maximum_channel_difference"] = _finite_number(
                exact["maximum_channel_difference"],
                minimum=0.0,
                maximum=255.0,
                code="invalid_maximum_channel_difference",
            )
        normalized_root["exact_validation"] = clean_exact

    if "test_suites" in root:
        suites = _require_mapping(root["test_suites"], "test_suites_must_be_object")
        _reject_unknown_keys(suites, _SUITE_KEYS)
        clean_suites: dict[str, str] = {}
        for key, value in suites.items():
            if value not in SUITE_STATUSES:
                raise SummaryValidationError("invalid_test_suite_status")
            clean_suites[key] = value
        normalized_root["test_suites"] = clean_suites
    return normalized_root


def _gate(status: str, observed: Any, threshold: str, detail: str) -> dict[str, Any]:
    return {"status": status, "observed": observed, "threshold": threshold, "detail": detail}


def _metric_values(cases: Sequence[Mapping[str, Any]], key: str) -> list[Any]:
    return [case.get("metrics", {}).get(key) for case in cases]


def _complete(values: Sequence[Any]) -> bool:
    return len(values) == 40 and all(value is not None for value in values)


def _one_sided_sign_test_pvalue(differences: Sequence[float]) -> float | None:
    signs = [difference for difference in differences if difference != 0]
    if not signs:
        return None
    positive = sum(difference > 0 for difference in signs)
    sample_size = len(signs)
    return sum(math.comb(sample_size, k) for k in range(positive, sample_size + 1)) / (
        2**sample_size
    )


def aggregate_summary(document: Any) -> dict[str, Any]:
    """Return a deterministic hard-gate summary from a validated input document."""

    validated = validate_summary(document)
    cases = validated["cases"]
    gates: dict[str, dict[str, Any]] = {}

    status_counts = dict.fromkeys(("passed", "failed", "skipped", "unverified"), 0)
    for case in cases:
        status_counts[case["status"]] += 1
    success_count = status_counts["passed"]
    gates["success_count"] = _gate(
        "passed" if success_count >= 38 else "failed",
        f"{success_count}/40",
        ">=38/40",
        "案例状态为 passed 才计入成功数。",
    )

    edge_values = _metric_values(cases, "edge_dice")
    if _complete(edge_values):
        edge_median = statistics.median(edge_values)
        gates["edge_dice_median"] = _gate(
            "passed" if edge_median >= 0.90 else "failed",
            edge_median,
            ">=0.90",
            "基于全部 40 张正式 SVG 原分辨率渲染摘要。",
        )
    else:
        gates["edge_dice_median"] = _gate(
            "unverified", None, ">=0.90", "缺少一张或多张正式渲染 Edge Dice 证据。"
        )

    mae_values = _metric_values(cases, "normalized_mae")
    if _complete(mae_values):
        mae_median = statistics.median(mae_values)
        gates["normalized_mae_median"] = _gate(
            "passed" if mae_median <= 0.08 else "failed",
            mae_median,
            "<=0.08",
            "基于全部 40 张正式 SVG 原分辨率渲染摘要。",
        )
    else:
        gates["normalized_mae_median"] = _gate(
            "unverified", None, "<=0.08", "缺少一张或多张正式渲染 normalized MAE 证据。"
        )

    seam_values = _metric_values(cases, "seam_free_4x")
    if _complete(seam_values):
        seam_count = sum(seam_values)
        gates["seam_free_4x"] = _gate(
            "passed" if seam_count / 40 >= 0.80 else "failed",
            f"{seam_count}/40",
            ">=80%",
            "仅统计 4 倍检查明确为无明显白缝的案例。",
        )
    else:
        gates["seam_free_4x"] = _gate(
            "unverified", None, ">=80%", "缺少一张或多张 4 倍白缝检查证据。"
        )

    anchors = _metric_values(cases, "anchor_count")
    baseline_anchors = _metric_values(cases, "artisan_baseline_anchor_count")
    baseline_edges = _metric_values(cases, "artisan_baseline_edge_dice")
    if _complete(anchors) and _complete(baseline_anchors):
        anchor_median = statistics.median(anchors)
        baseline_anchor_median = statistics.median(baseline_anchors)
        if baseline_anchor_median > 0:
            ratio = anchor_median / baseline_anchor_median
        elif anchor_median == 0:
            ratio = 1.0
        else:
            ratio = math.inf
        primary_passed = baseline_anchor_median > 0 and ratio <= 0.75
        sign_pvalue: float | None = None
        median_edge_delta: float | None = None
        alternate_passed = False
        alternate_anchor_limit_passed = anchor_median <= baseline_anchor_median * 1.10
        if alternate_anchor_limit_passed and _complete(edge_values) and _complete(baseline_edges):
            edge_differences = [
                current - baseline for current, baseline in zip(edge_values, baseline_edges)
            ]
            median_edge_delta = statistics.median(edge_differences)
            sign_pvalue = _one_sided_sign_test_pvalue(edge_differences)
            alternate_passed = (
                median_edge_delta > 0 and sign_pvalue is not None and sign_pvalue < 0.05
            )
        gates["anchor_rule"] = _gate(
            "passed" if primary_passed or alternate_passed else "failed",
            {
                "anchor_median": anchor_median,
                "artisan_baseline_anchor_median": baseline_anchor_median,
                "ratio": ratio if math.isfinite(ratio) else None,
                "median_edge_dice_delta": median_edge_delta,
                "one_sided_sign_test_pvalue": sign_pvalue,
            },
            "锚点中位数减少>=25%，或锚点不增加>10%且配对 Edge Dice 单侧符号检验 p<0.05",
            "备用规则同时要求 Edge Dice 差值中位数大于 0。",
        )
    else:
        gates["anchor_rule"] = _gate(
            "unverified", None, "主规则或备用规则", "缺少一张或多张锚点基线/结果证据。"
        )

    safety_values = _metric_values(cases, "safe_svg")
    known_unsafe = any(
        any(value.get(key) is False for key in _SAFE_SVG_KEYS)
        for value in safety_values
        if isinstance(value, Mapping)
    )
    complete_safety = _complete(safety_values) and all(
        isinstance(value, Mapping) and set(value) == _SAFE_SVG_KEYS for value in safety_values
    )
    if known_unsafe:
        safe_count = sum(
            isinstance(value, Mapping) and set(value) == _SAFE_SVG_KEYS and all(value.values())
            for value in safety_values
        )
        gates["safe_svg"] = _gate(
            "failed",
            f"{safe_count}/40",
            "40/40 无位图、脚本和外链",
            "至少一张正式 SVG 的禁止项验证明确失败。",
        )
    elif not complete_safety:
        gates["safe_svg"] = _gate(
            "unverified",
            None,
            "40/40 无位图、脚本和外链",
            "缺少一张或多张正式 SVG 安全验证证据。",
        )
    else:
        gates["safe_svg"] = _gate(
            "passed",
            "40/40",
            "40/40 无位图、脚本和外链",
            "全部正式 SVG 均有完整且通过的禁止项验证证据。",
        )

    exact = validated.get("exact_validation")
    if not exact or set(exact) != _EXACT_KEYS:
        gates["exact_pixel_validation"] = _gate(
            "unverified",
            None,
            "pixel_match=true、different_pixel_count=0、maximum_channel_difference=0",
            "Exact 像素验证证据不完整。",
        )
    else:
        exact_passed = (
            exact["pixel_match"] is True
            and exact["different_pixel_count"] == 0
            and exact["maximum_channel_difference"] == 0
        )
        gates["exact_pixel_validation"] = _gate(
            "passed" if exact_passed else "failed",
            exact,
            "pixel_match=true、different_pixel_count=0、maximum_channel_difference=0",
            "Exact 三项必须同时保持精确值。",
        )

    suites = validated.get("test_suites", {})
    if set(suites) != _SUITE_KEYS:
        suites_status = "unverified"
        suites_detail = "Python、前端或 Rust 测试证据不完整。"
    elif any(value == "failed" for value in suites.values()):
        suites_status = "failed"
        suites_detail = "至少一个全量测试套件失败。"
    elif all(value == "passed" for value in suites.values()):
        suites_status = "passed"
        suites_detail = "Python、前端和 Rust 全量测试均有通过证据。"
    else:
        suites_status = "unverified"
        suites_detail = "存在跳过或未验证的全量测试套件。"
    gates["test_suites"] = _gate(
        suites_status,
        suites or None,
        "Python、前端、Rust 全部 passed",
        suites_detail,
    )

    gate_counts = dict.fromkeys(("passed", "failed", "unverified"), 0)
    for gate in gates.values():
        gate_counts[gate["status"]] += 1
    if gate_counts["failed"]:
        overall_status = "failed"
    elif gate_counts["unverified"]:
        overall_status = "unverified"
    else:
        overall_status = "passed"

    return {
        "schema_version": SCHEMA_VERSION,
        "benchmark": "CreNexus Vector60",
        "overall_status": overall_status,
        "case_counts": status_counts,
        "gate_counts": gate_counts,
        "gates": {key: gates[key] for key in _GATE_ORDER},
        "comparisons": [
            {
                "case_id": case["case_id"],
                "status": "unverified",
                "relative_ref": f"comparisons/{case['category']}/{case['case_id']}.png",
            }
            for case in cases
        ],
    }


def _display(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.6g}"
    if isinstance(value, Mapping):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return str(value)


def render_markdown(result: Mapping[str, Any]) -> str:
    """Render an aggregate result without embedding input paths or artifact content."""

    lines = [
        "# CreNexus Vector60 基准报告",
        "",
        f"总状态：`{result['overall_status']}`",
        "",
        "本报告只汇总脱敏的逐图 JSON 摘要；不包含源素材、用户路径、账号状态或凭据。",
        "",
        "## 硬门",
        "",
        "| 硬门 | 状态 | 观测值 | 门槛 | 说明 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for name in _GATE_ORDER:
        gate = result["gates"][name]
        lines.append(
            f"| `{name}` | `{gate['status']}` | {_display(gate['observed'])} | "
            f"{gate['threshold']} | {gate['detail']} |"
        )
    lines.extend(
        [
            "",
            "## 案例状态",
            "",
            "| 通过 | 失败 | 跳过 | 未验证 |",
            "| ---: | ---: | ---: | ---: |",
            "| {passed} | {failed} | {skipped} | {unverified} |".format(**result["case_counts"]),
            "",
            "## 前后对比图预留",
            "",
            "以下仅是脱敏相对引用约定，不代表对应图片已生成或已验证。不得提交源素材或临时渲染。",
            "",
        ]
    )
    for comparison in result["comparisons"]:
        relative_ref = comparison["relative_ref"]
        if not _COMPARISON_REF_RE.fullmatch(relative_ref):
            raise SummaryValidationError("unsafe_comparison_reference")
        lines.append(
            f"- `{comparison['case_id']}`：`{comparison['status']}`；预留 `{relative_ref}`"
        )
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Aggregate a privacy-safe Vector60 per-case JSON summary."
    )
    parser.add_argument("--input", required=True, help="Redacted vector60-summary-v1 JSON file")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        document = json.loads(Path(args.input).read_text(encoding="utf-8"))
        result = aggregate_summary(document)
        if args.format == "markdown":
            sys.stdout.write(render_markdown(result))
        else:
            json.dump(result, sys.stdout, ensure_ascii=False, sort_keys=True)
            sys.stdout.write("\n")
    except (OSError, UnicodeError, json.JSONDecodeError, SummaryValidationError):
        sys.stderr.write('{"ok":false,"error":"invalid_or_unreadable_summary"}\n')
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
