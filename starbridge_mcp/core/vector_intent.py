from __future__ import annotations

import re
from typing import Any

from starbridge_mcp.core.security import sanitize

TASK_ALIASES = {
    "照图重绘": "reference_vector_rebuild",
    "照着画": "reference_vector_rebuild",
    "按图画": "reference_vector_rebuild",
    "图标重绘": "icon_rebuild",
    "线稿转矢量": "line_art_vectorization",
    "剪影重建": "silhouette_rebuild",
}
STRATEGY_ALIASES = {
    "语义重建": "semantic_reconstruction",
    "轮廓重建": "contour_reconstruction",
    "几何重建": "geometric_reconstruction",
}
CONFLICTS = (
    ("不用描摹", "允许描摹"),
    ("文字可编", "文字转曲"),
    ("无渐变", "保留渐变"),
    ("保持原色", "品牌色优先"),
    ("只预览", "确认执行"),
)


def default_vector_task() -> dict[str, Any]:
    return {
        "schema_version": "starbridge.vector-task.v1",
        "task": "reference_vector_rebuild",
        "strategy": "semantic_reconstruction",
        "structure": {
            "semantic_layers": True,
            "anchor_policy": "minimal",
            "live_text": True,
            "reuse_symbols": True,
            "image_trace": False,
        },
        "style": {
            "max_colors": None,
            "gradient_allowed": True,
            "color_policy": "reference_match",
        },
        "quality": {
            "overall_min": 90,
            "dimension_min": 75,
            "priority": [
                "silhouette",
                "proportion",
                "negative_space",
                "topology",
                "visual_detail",
            ],
            "negative_space_hard_gate": False,
            "topology_hard_gate": True,
        },
        "review": {
            "preview_required": True,
            "max_repair_rounds": 2,
            "patch_mode": "diff_only",
        },
        "exports": ["svg"],
        "dry_run": True,
        "confirm_write": False,
        "unrecognized_terms": [],
    }


def _segments(command: str) -> list[str]:
    return [item.strip() for item in re.split(r"[|｜+]", command) if item.strip()]


def _contains_any(term: str, candidates: tuple[str, ...] | list[str]) -> bool:
    return any(candidate in term for candidate in candidates)


def parse_vector_command(command: str) -> dict[str, Any]:
    raw = command.strip()
    if not raw:
        return sanitize(
            {
                "ok": False,
                "action": "vector_intent_parse",
                "message": "vector command must not be empty",
                "conflicts": [],
                "task": None,
            }
        )

    conflicts = [[left, right] for left, right in CONFLICTS if left in raw and right in raw]
    if conflicts:
        return sanitize(
            {
                "ok": False,
                "action": "vector_intent_parse",
                "message": "conflicting vector command constraints",
                "conflicts": conflicts,
                "task": None,
            }
        )

    task = default_vector_task()
    recognized_markers = set(TASK_ALIASES) | set(STRATEGY_ALIASES) | {
        "分层",
        "少节点",
        "文字可编",
        "文字转曲",
        "组件复用",
        "不用描摹",
        "允许描摹",
        "无渐变",
        "保留渐变",
        "保持原色",
        "品牌色优先",
        "轮廓优先",
        "负形必准",
        "拓扑必过",
        "只修差异",
        "先预览",
        "只预览",
        "SVG",
        "PDF",
        "PNG",
    }

    for alias, value in TASK_ALIASES.items():
        if alias in raw:
            task["task"] = value
            break
    for alias, value in STRATEGY_ALIASES.items():
        if alias in raw:
            task["strategy"] = value
            break

    structure = task["structure"]
    style = task["style"]
    quality = task["quality"]
    review = task["review"]
    if "分层" in raw:
        structure["semantic_layers"] = True
    if "少节点" in raw:
        structure["anchor_policy"] = "minimal"
    if "文字可编" in raw:
        structure["live_text"] = True
    if "文字转曲" in raw:
        structure["live_text"] = False
    if "组件复用" in raw:
        structure["reuse_symbols"] = True
    if "允许描摹" in raw:
        structure["image_trace"] = True
    if "不用描摹" in raw:
        structure["image_trace"] = False
    if "无渐变" in raw:
        style["gradient_allowed"] = False
    if "保留渐变" in raw:
        style["gradient_allowed"] = True
    if "保持原色" in raw:
        style["color_policy"] = "reference_match"
    if "品牌色优先" in raw:
        style["color_policy"] = "brand_tokens"
    if "轮廓优先" in raw:
        quality["priority"] = [
            "silhouette",
            "proportion",
            "negative_space",
            "topology",
            "visual_detail",
        ]
    if "负形必准" in raw or "轮廓负形必准" in raw:
        quality["negative_space_hard_gate"] = True
    if "拓扑必过" in raw:
        quality["topology_hard_gate"] = True
    if "只修差异" in raw:
        review["patch_mode"] = "diff_only"

    color_match = re.search(r"限?(\d{1,2})色", raw)
    if color_match:
        style["max_colors"] = max(1, min(32, int(color_match.group(1))))
    quality_match = re.search(r"五维\s*(\d{1,3})分?", raw)
    if quality_match:
        quality["overall_min"] = max(0, min(100, int(quality_match.group(1))))
    repair_match = re.search(r"修\s*(\d)轮", raw)
    if repair_match:
        review["max_repair_rounds"] = max(0, min(3, int(repair_match.group(1))))

    exports = [name.lower() for name in ("SVG", "PDF", "PNG") if name in raw.upper()]
    if exports:
        task["exports"] = exports

    numeric_patterns = (r"陟?\d{1,2}色", r"五维\s*\d{1,3}分?", r"修\s*\d轮")
    unrecognized: list[str] = []
    for term in _segments(raw):
        known = _contains_any(term, tuple(recognized_markers)) or any(
            re.search(pattern, term) for pattern in numeric_patterns
        )
        if not known:
            unrecognized.append(term)
    task["unrecognized_terms"] = unrecognized

    return sanitize(
        {
            "ok": True,
            "action": "vector_intent_parse",
            "message": "vector command parsed as a safe dry-run task",
            "conflicts": [],
            "task": task,
        }
    )


def validate_vector_task(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    required = {
        "schema_version",
        "task",
        "strategy",
        "structure",
        "style",
        "quality",
        "review",
        "exports",
        "dry_run",
        "confirm_write",
        "unrecognized_terms",
    }
    missing = sorted(required - set(payload))
    if missing:
        return [f"missing fields: {', '.join(missing)}"]
    if payload["schema_version"] != "starbridge.vector-task.v1":
        failures.append("unsupported schema_version")
    if payload["task"] not in set(TASK_ALIASES.values()):
        failures.append("unsupported vector task")
    if payload["strategy"] not in set(STRATEGY_ALIASES.values()):
        failures.append("unsupported reconstruction strategy")
    if payload["dry_run"] is not True or payload["confirm_write"] is not False:
        failures.append("VectorTask v1 must remain dry-run and unconfirmed")
    if not payload["exports"] or not set(payload["exports"]).issubset({"svg", "pdf", "png"}):
        failures.append("exports must contain supported formats")
    max_colors = payload["style"].get("max_colors")
    if max_colors is not None and not 1 <= max_colors <= 32:
        failures.append("max_colors must be between 1 and 32")
    rounds = payload["review"].get("max_repair_rounds")
    if not isinstance(rounds, int) or not 0 <= rounds <= 3:
        failures.append("max_repair_rounds must be between 0 and 3")
    return failures
