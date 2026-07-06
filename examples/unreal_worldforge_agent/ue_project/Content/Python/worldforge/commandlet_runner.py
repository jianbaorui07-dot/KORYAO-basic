"""Entry points used by UnrealEditor-Cmd Python commandlet scripts."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from . import asset_probe
from .execution_logger import ExecutionLogger
from . import memory_guard


def get_paths() -> tuple[Path, Path, str]:
    project_root = Path(os.environ.get("WORLDFORGE_PROJECT_ROOT", memory_guard.project_root_from_env())).resolve()
    job_id = os.environ.get("WORLDFORGE_JOB_ID", "WF0009_v1_1_probe")
    ledger = Path(os.environ.get("WORLDFORGE_LEDGER_DIR", project_root / "Saved" / "WorldForge" / "RunLedger" / job_id)).resolve()
    ledger.mkdir(parents=True, exist_ok=True)
    return project_root, ledger, job_id


def run_probe() -> dict:
    project_root, ledger, job_id = get_paths()
    logger = ExecutionLogger(ledger)
    try:
        (ledger / "job.json").write_text(
            json.dumps(
                {
                    "job_id": job_id,
                    "route": "LEVEL_1_COMMANDLET_PROBE",
                    "project_root": str(project_root),
                    "status": "running",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        memory_guard.write_memory_profile(ledger / "memory_profile.json", {"phase": "commandlet_probe_start"})
        result = asset_probe.create_probe_assets(project_root, ledger, job_id)
        final_status = "commandlet_probe_passed" if result.get("status") == "passed" else "failed"
        (ledger / "final_receipt.json").write_text(
            json.dumps(
                {
                    "job_id": job_id,
                    "status": final_status,
                    "completion": "not_completed",
                    "probe_result": "commandlet_probe_result.json",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return result
    except BaseException as exc:
        logger.exception("commandlet_probe_exception", exc)
        (ledger / "final_receipt.json").write_text(
            json.dumps(
                {
                    "job_id": job_id,
                    "status": "failed",
                    "completion": "not_completed",
                    "error": str(exc),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        raise


if __name__ == "__main__":
    output = run_probe()
    print(output)
