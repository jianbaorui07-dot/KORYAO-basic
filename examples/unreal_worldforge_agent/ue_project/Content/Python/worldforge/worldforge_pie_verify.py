"""Short PIE verification helper."""

from __future__ import annotations

import time


def run_short_pie(max_seconds: int = 45) -> dict:
    try:
        import unreal  # type: ignore
    except Exception as exc:
        return {"attempted": False, "started": False, "reason": f"unreal module unavailable: {exc}"}
    duration = min(max_seconds, 8)
    try:
        unreal.EditorLevelLibrary.editor_play_simulate()
        time.sleep(duration)
        unreal.EditorLevelLibrary.editor_end_play()
    except Exception as exc:
        return {
            "attempted": True,
            "started": False,
            "duration_seconds": 0,
            "reason": str(exc),
            "player_movement_verified": False,
            "interaction_verified": False,
        }
    return {
        "attempted": True,
        "started": True,
        "duration_seconds": duration,
        "player_movement_verified": False,
        "interaction_verified": False,
        "note": "PIE was started and stopped by automation, but no trustworthy movement or overlap evidence is claimed.",
    }
