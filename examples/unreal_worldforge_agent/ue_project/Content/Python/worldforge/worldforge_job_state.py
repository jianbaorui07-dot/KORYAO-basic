"""WorldForge job state machine helper."""

from __future__ import annotations

import json
from pathlib import Path


NORMAL_STATES = [
    "draft",
    "specified",
    "planned",
    "preflight_passed",
    "commandlet_probe_passed",
    "microbuild_running",
    "assets_saved",
    "assets_verified",
    "editor_build_running",
    "PIE_verified",
    "preview_verified",
    "completed",
]
TERMINAL_STATES = ["blocked", "failed", "rolled_back", "cancelled"]


def can_transition(current: str, target: str) -> bool:
    if current in TERMINAL_STATES:
        return False
    if target in TERMINAL_STATES:
        return True
    if current not in NORMAL_STATES or target not in NORMAL_STATES:
        return False
    return NORMAL_STATES.index(target) >= NORMAL_STATES.index(current)


def write_state(path: str | Path, job_id: str, state: str, reason: str = "") -> Path:
    if state not in NORMAL_STATES + TERMINAL_STATES:
        raise ValueError(f"invalid WorldForge state: {state}")
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps({"job_id": job_id, "state": state, "reason": reason}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return out
