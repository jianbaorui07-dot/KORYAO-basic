from __future__ import annotations

import base64
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .schemas import ADAPTER_NAME, ADAPTER_VERSION, EvidenceManifest

_PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wn13dQAAAAASUVORK5CYII="
)

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def new_job_id() -> str:
    return uuid4().hex[:12]


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_placeholder_png(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_PNG_1X1)


def manifest_path_for(base_dir: Path, tool_name: str, job_id: str) -> Path:
    slug = tool_name.replace(".", "_")
    return base_dir / f"{slug}_{job_id}_manifest.json"


def preview_path_for(base_dir: Path, job_id: str) -> Path:
    return base_dir / f"ps_preview_{job_id}.png"


def read_png_dimensions(data: bytes) -> tuple[int, int]:
    if not data.startswith(_PNG_SIGNATURE):
        raise ValueError("file is not a PNG (signature mismatch)")
    if len(data) < 24:
        raise ValueError("PNG payload is too short to contain an IHDR chunk")
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    return width, height


def build_output_artifact(
    path: Path,
    *,
    repo_root: Path,
    format_hint: str = "png",
    document_name: str | None = None,
    width_hint: int | None = None,
    height_hint: int | None = None,
) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"expected output artifact does not exist: {path}")
    data = path.read_bytes()
    sha256 = hashlib.sha256(data).hexdigest()
    width: int | None = width_hint
    height: int | None = height_hint
    fmt = format_hint
    if data.startswith(_PNG_SIGNATURE):
        png_w, png_h = read_png_dimensions(data)
        width, height = png_w, png_h
        fmt = "png"
    try:
        relative = path.relative_to(repo_root).as_posix()
    except ValueError:
        relative = path.as_posix()
    return {
        "relative_path": relative,
        "absolute_path": path.as_posix(),
        "format": fmt,
        "bytes": len(data),
        "sha256": sha256,
        "width": width,
        "height": height,
        "document_name": document_name,
        "verified_at": utc_now_iso(),
    }


def build_manifest(
    *,
    job_id: str,
    tool_name: str,
    risk_level: str,
    requires_confirmation: bool,
    dry_run: bool,
    input_summary: dict,
    output_files: list[str],
    preview_files: list[str],
    source_files: list[str],
    photoshop_available: bool,
    bridge_kind: str,
    node_proxy_status: dict,
    uxp_status: dict,
    photoshop_host: dict,
    layers_snapshot: list[dict],
    history_state: str | None,
    descriptor_summary: list[dict],
    validation_result: dict,
    status: str,
    warnings: list[str],
    errors: list[str],
    output_artifacts: list[dict] | None = None,
) -> EvidenceManifest:
    return EvidenceManifest(
        job_id=job_id,
        created_at=utc_now_iso(),
        adapter_name=ADAPTER_NAME,
        adapter_version=ADAPTER_VERSION,
        tool_name=tool_name,
        risk_level=risk_level,
        requires_confirmation=requires_confirmation,
        dry_run=dry_run,
        input_summary=input_summary,
        output_files=output_files,
        preview_files=preview_files,
        source_files=source_files,
        photoshop_available=photoshop_available,
        bridge_kind=bridge_kind,
        node_proxy_status=node_proxy_status,
        uxp_status=uxp_status,
        photoshop_host=photoshop_host,
        layers_snapshot=layers_snapshot,
        history_state=history_state,
        descriptor_summary=descriptor_summary,
        validation_result=validation_result,
        status=status,
        warnings=warnings,
        errors=errors,
        output_artifacts=list(output_artifacts or []),
    )
