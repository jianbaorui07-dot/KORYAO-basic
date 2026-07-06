"""WorldSpec loading and lightweight validation."""

from __future__ import annotations

import json
from pathlib import Path


REQUIRED_KEYS = [
    "world_id",
    "revision",
    "title",
    "template",
    "world_scale",
    "editable",
    "playable",
    "reference_images",
    "visual_style",
    "environment",
    "required_assets",
    "interactive_rules",
    "performance_profile",
    "completion_gates",
]


def default_spec_path(project_dir: Path) -> Path:
    return project_dir / "Content" / "WorldForge" / "Specs" / "WF0009_v0.9-real.worldspec.json"


def load_worldspec(path: str | Path) -> dict:
    spec_path = Path(path)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    errors = validate_worldspec(spec)
    if errors:
        raise ValueError("WorldSpec validation failed: " + "; ".join(errors))
    return spec


def validate_worldspec(spec: dict) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED_KEYS:
        if key not in spec:
            errors.append(f"missing required key: {key}")
    if spec.get("world_id") != "WF-0009":
        errors.append("this job runner currently expects world_id WF-0009")
    if spec.get("template") != "SnowTemple":
        errors.append("this job runner currently expects template SnowTemple")
    if not isinstance(spec.get("required_assets", []), list):
        errors.append("required_assets must be a list")
    return errors
