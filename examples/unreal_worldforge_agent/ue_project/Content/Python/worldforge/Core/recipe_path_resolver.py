"""Resolve WorldForge recipe paths without exposing JSON to UE Content import."""

from __future__ import annotations

from pathlib import Path


def recipe_root(project_root: str | Path) -> Path:
    return Path(project_root).resolve() / "Config" / "WorldForge" / "Recipes"


def resolve(requested_path: str | Path, project_root: str | Path) -> Path:
    """Map legacy Content/Python recipe JSON requests to Config/WorldForge/Recipes."""
    requested = Path(requested_path)
    if requested.exists():
        return requested.resolve()
    candidate = recipe_root(project_root) / requested.name
    if candidate.exists():
        return candidate.resolve()
    if "Content" in requested.parts and requested.suffix.lower() == ".json":
        legacy_candidate = recipe_root(project_root) / requested.name
        if legacy_candidate.exists():
            return legacy_candidate.resolve()
    raise FileNotFoundError(f"WorldForge recipe not found: {requested_path}")
