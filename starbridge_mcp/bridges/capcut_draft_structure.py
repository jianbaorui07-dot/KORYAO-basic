from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from starbridge_mcp.core.security import sanitize


SENSITIVE_DRAFT_FILES = {"draft_content.json", "draft_info.json"}


def _configured_dirs() -> list[tuple[str, str]]:
    pairs = []
    for name in ("JIANYING_DRAFTS_DIR", "CAPCUT_DRAFTS_DIR"):
        value = os.environ.get(name)
        if value:
            pairs.append((name, value))
    return pairs


def draft_structure_summary(*, max_entries: int = 25) -> dict[str, Any]:
    configured = _configured_dirs()
    roots = []
    warnings = []
    for env_name, raw_path in configured:
        path = Path(raw_path)
        exists = path.exists()
        entry_count = 0
        directory_count = 0
        sensitive_markers: set[str] = set()
        if exists and path.is_dir():
            for index, child in enumerate(path.iterdir()):
                if index >= max_entries:
                    warnings.append(f"{env_name} entry scan truncated at {max_entries}.")
                    break
                entry_count += 1
                if child.is_dir():
                    directory_count += 1
                if child.name in SENSITIVE_DRAFT_FILES:
                    sensitive_markers.add(child.name)
        roots.append(
            {
                "env": env_name,
                "configured": True,
                "exists": exists,
                "is_dir": path.is_dir() if exists else False,
                "entry_count_sample": entry_count,
                "directory_count_sample": directory_count,
                "sensitive_marker_names_detected": sorted(sensitive_markers),
            }
        )

    if not configured:
        warnings.append("No draft directory environment variables are configured.")

    return sanitize(
        {
            "ok": any(item["exists"] and item["is_dir"] for item in roots),
            "bridge": "jianying_capcut",
            "action": "draft_structure",
            "mode": "redacted_summary",
            "roots": roots,
            "warnings": warnings,
            "safety_policy": {
                "recursive_scan": False,
                "draft_json_read": False,
                "draft_names_printed": False,
                "media_paths_printed": False,
                "desktop_app_control": False,
                "video_export": False,
            },
            "next_steps": [
                "Configure JIANYING_DRAFTS_DIR or CAPCUT_DRAFTS_DIR for local-only structure checks.",
                "Keep draft metadata files, subtitles, media paths, and account state out of public reports.",
            ],
        }
    )
