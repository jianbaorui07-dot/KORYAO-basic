"""Resource policy and preflight checks for WorldForge recipes."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import state_manager


RUNTIME_ROOT = Path(r"<WORLDFORGE_RUNTIME>")
DDC_PATH = RUNTIME_ROOT / "DDC"
LOGS_PATH = RUNTIME_ROOT / "Logs"
PREVIEWS_PATH = RUNTIME_ROOT / "Previews"
RECEIPTS_PATH = RUNTIME_ROOT / "Receipts"


@dataclass(frozen=True)
class ResourcePolicy:
    name: str
    max_actor_count: int
    min_memory_gb: float
    allow_external_assets: bool
    allow_world_partition: bool
    allow_pcg: bool
    allow_niagara: bool


P1_LIGHTWEIGHT = ResourcePolicy(
    name="P1_LIGHTWEIGHT",
    max_actor_count=32,
    min_memory_gb=4.0,
    allow_external_assets=False,
    allow_world_partition=False,
    allow_pcg=False,
    allow_niagara=False,
)

P2_STANDARD = ResourcePolicy(
    name="P2_STANDARD",
    max_actor_count=96,
    min_memory_gb=6.0,
    allow_external_assets=False,
    allow_world_partition=False,
    allow_pcg=False,
    allow_niagara=True,
)


def ensure_runtime_dirs() -> dict[str, str]:
    for path in (DDC_PATH, LOGS_PATH, PREVIEWS_PATH, RECEIPTS_PATH):
        path.mkdir(parents=True, exist_ok=True)
    return {
        "ddc_path": str(DDC_PATH),
        "logs_path": str(LOGS_PATH),
        "previews_path": str(PREVIEWS_PATH),
        "receipts_path": str(RECEIPTS_PATH),
    }


def select_policy(recipe: dict[str, Any]) -> ResourcePolicy:
    mode = str(recipe.get("mode", "P1_LIGHTWEIGHT")).upper()
    if mode.startswith("P2"):
        return P2_STANDARD
    return P1_LIGHTWEIGHT


def preflight(recipe: dict[str, Any], project_root: Path | None = None) -> dict[str, Any]:
    root = project_root or state_manager.project_root()
    runtime = ensure_runtime_dirs()
    policy = select_policy(recipe)
    memory_gb = state_manager.free_memory_gb()
    c_drive_gb = state_manager.c_drive_free_gb()
    constraints = recipe.get("constraints", {})
    ok = True
    issues: list[str] = []
    if memory_gb >= 0 and memory_gb < policy.min_memory_gb:
        ok = False
        issues.append(f"memory_below_{policy.min_memory_gb}gb")
    if not Path(root).exists():
        ok = False
        issues.append("project_root_missing")
    if constraints.get("external_assets") and not policy.allow_external_assets:
        ok = False
        issues.append("external_assets_not_allowed_by_policy")
    return {
        "ok": ok,
        "issues": issues,
        "policy": policy.__dict__,
        "runtime": runtime,
        "available_memory_gb": memory_gb,
        "c_drive_free_gb": c_drive_gb,
    }
