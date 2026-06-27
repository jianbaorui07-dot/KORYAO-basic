from __future__ import annotations

from typing import Any

from starbridge_mcp.core.security import sanitize


def preflight_summary(document_summary: dict[str, Any] | None = None) -> dict[str, Any]:
    summary = document_summary or {}
    artboards = int(summary.get("artboards") or summary.get("artboard_count") or 0)
    linked_assets = int(summary.get("linked_assets") or summary.get("placed_items") or 0)
    missing_links = int(summary.get("missing_links") or 0)
    text_objects = int(summary.get("text_objects") or summary.get("text_frames") or 0)
    color_mode = str(summary.get("color_mode") or summary.get("document_color_space") or "unknown")

    checks = [
        {
            "name": "active_document",
            "ok": bool(summary),
            "severity": "info" if summary else "needs_user",
        },
        {"name": "artboards_present", "ok": artboards > 0 if summary else None, "severity": "warn"},
        {
            "name": "missing_links",
            "ok": missing_links == 0 if summary else None,
            "severity": "error",
        },
        {
            "name": "linked_assets_counted",
            "ok": linked_assets >= 0 if summary else None,
            "severity": "info",
        },
        {
            "name": "text_objects_counted",
            "ok": text_objects >= 0 if summary else None,
            "severity": "info",
        },
        {
            "name": "color_mode_known",
            "ok": color_mode.lower() in {"rgb", "cmyk"} if summary else None,
            "severity": "warn",
        },
    ]
    warnings = []
    if not summary:
        warnings.append(
            "No document_summary was supplied; returning a safe preflight checklist only."
        )
    if missing_links:
        warnings.append("Missing linked assets were reported by the provided summary.")
    if color_mode == "unknown" and summary:
        warnings.append("Color mode is unknown; inspect the active Illustrator document locally.")

    return sanitize(
        {
            "ok": not any(item["ok"] is False and item["severity"] == "error" for item in checks),
            "bridge": "illustrator",
            "action": "preflight",
            "mode": "metadata_only",
            "summary": {
                "artboards": artboards,
                "linked_assets": linked_assets,
                "missing_links": missing_links,
                "text_objects": text_objects,
                "color_mode": color_mode,
            },
            "checks": checks,
            "warnings": warnings,
            "safety_policy": {
                "opens_ai_file": False,
                "exports_assets": False,
                "prints_source_paths": False,
                "requires_active_authorized_illustrator_for_live_summary": True,
            },
            "next_steps": [
                "Run illustrator.document_info on a local authorized Illustrator session, then pass its summary into this preflight.",
                "Keep source image paths, linked file paths, fonts, and export directories out of public reports.",
            ],
        }
    )
