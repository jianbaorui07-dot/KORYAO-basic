from __future__ import annotations

import hashlib
import http.client
import json
import uuid
from collections.abc import Callable
from typing import Any
from urllib.parse import urlsplit

from starbridge_mcp.core.job_snapshot_schema import (
    JOB_STATUSES,
    MAX_OUTPUTS_COUNT,
    SCHEMA_VERSION,
)
from starbridge_mcp.core.progress_monitor import _direct_loopback_socket
from starbridge_mcp.core.queue_snapshot import DEFAULT_COMFY_URL, _validate_loopback_url
from starbridge_mcp.core.security import sanitize

MAX_JOB_BYTES = 1_048_576
ENDPOINT_TEMPLATE = "/api/jobs/{job_id}"


class JobEndpointUnavailable(OSError):
    """Raised when the bounded local job route cannot be used safely."""


class JobNotFound(LookupError):
    """Raised when ComfyUI confirms that the requested job does not exist."""


class JobPayloadInvalid(ValueError):
    """Raised when the local job response is malformed or exceeds safe bounds."""


JobFetcher = Callable[[str, str, int], dict[str, Any]]


def _validate_job_id(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("job_id must be a canonical lowercase UUID")
    try:
        normalized = str(uuid.UUID(value))
    except (ValueError, AttributeError) as exc:
        raise ValueError("job_id must be a canonical lowercase UUID") from exc
    if normalized != value:
        raise ValueError("job_id must be a canonical lowercase UUID")
    return value


def _logical_job_id(raw_job_id: str) -> str:
    digest = hashlib.sha256(raw_job_id.encode("utf-8")).hexdigest()[:12]
    return f"job_{digest}"


def _decode_json(raw: bytes) -> Any:
    if len(raw) > MAX_JOB_BYTES:
        raise JobPayloadInvalid("job payload exceeds the safe response limit")
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise JobPayloadInvalid("job payload must be valid UTF-8 JSON") from exc


def _read_job(base_url: str, job_id: str, timeout: int) -> dict[str, Any]:
    parsed = urlsplit(base_url)
    hostname = parsed.hostname
    if hostname is None:
        raise JobEndpointUnavailable("loopback job endpoint unavailable")
    port = parsed.port or 80
    direct_socket = _direct_loopback_socket(base_url, timeout)
    connection = http.client.HTTPConnection(hostname, port, timeout=timeout)
    connection.sock = direct_socket
    try:
        connection.request(
            "GET",
            f"/api/jobs/{job_id}",
            headers={"Accept": "application/json", "Connection": "close"},
        )
        response = connection.getresponse()
        raw = response.read(MAX_JOB_BYTES + 1)
        content_type = response.getheader("Content-Type", "").partition(";")[0].strip().lower()
        if response.status == 404:
            if content_type == "application/json":
                payload = _decode_json(raw)
                if isinstance(payload, dict) and payload.get("error") == "Job not found":
                    raise JobNotFound("job not found")
            raise JobEndpointUnavailable("loopback job route unavailable")
        if response.status != 200 or content_type != "application/json":
            raise JobEndpointUnavailable("loopback job endpoint unavailable")
        payload = _decode_json(raw)
        if not isinstance(payload, dict):
            raise JobPayloadInvalid("job payload must be an object")
        return payload
    except (http.client.HTTPException, ConnectionError) as exc:
        raise JobEndpointUnavailable("loopback job endpoint unavailable") from exc
    finally:
        connection.close()


def normalize_job_payload(payload: Any, *, job_id: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise JobPayloadInvalid("job payload must be an object")
    if payload.get("id") != job_id:
        raise JobPayloadInvalid("job response id does not match the requested id")
    status = payload.get("status")
    if status not in JOB_STATUSES:
        raise JobPayloadInvalid("job status is unsupported")
    outputs_count = payload.get("outputs_count")
    if outputs_count is not None and (
        type(outputs_count) is not int or not 0 <= outputs_count <= MAX_OUTPUTS_COUNT
    ):
        raise JobPayloadInvalid("outputs_count must be a bounded non-negative integer")
    terminal = status in {"completed", "failed", "cancelled"}
    return {
        "logical_job_id": _logical_job_id(job_id),
        "status": status,
        "terminal": terminal,
        "completion_ready": terminal,
        "outputs_count": outputs_count,
    }


def _empty_job(job_id: str) -> dict[str, Any]:
    return {
        "logical_job_id": _logical_job_id(job_id),
        "status": None,
        "terminal": False,
        "completion_ready": False,
        "outputs_count": None,
    }


def _safety(*, network_access: bool) -> dict[str, Any]:
    return {
        "network_access": network_access,
        "loopback_only": True,
        "proxy_used": False,
        "redirects_followed": False,
        "single_job_only": True,
        "raw_job_ids_returned": False,
        "workflow_payloads_returned": False,
        "output_payloads_returned": False,
        "preview_payloads_returned": False,
        "error_details_returned": False,
        "raw_payload_retained": False,
        "history_endpoint_read": False,
        "job_mutation": False,
        "local_file_reads": False,
        "local_file_writes": False,
        "desktop_software_started": False,
    }


def _snapshot_id(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"jobstatus_{hashlib.sha256(canonical).hexdigest()[:12]}"


def _finalize(payload: dict[str, Any]) -> dict[str, Any]:
    payload["snapshot_id"] = _snapshot_id(payload)
    return sanitize(payload)


def job_snapshot_contract() -> dict[str, Any]:
    return {
        "tool": "comfyui.job_snapshot",
        "schema_version": SCHEMA_VERSION,
        "endpoint": ENDPOINT_TEMPLATE,
        "default_probe": False,
        "live_scope": "direct_loopback_single_job_http_only",
        "proxy_used": False,
        "redirects_followed": False,
        "raw_identifiers_returned": False,
        "workflow_payloads_returned": False,
        "output_payloads_returned": False,
        "history_endpoint_read": False,
        "job_mutation": False,
    }


def _next_steps(status: str) -> list[str]:
    return {
        "pending": [
            "Wait for queue capacity; do not submit another job from this read-only result."
        ],
        "in_progress": [
            "Continue bounded progress monitoring or request another job snapshot later."
        ],
        "completed": ["Record completion without reading private outputs or workflow content."],
        "failed": ["Inspect ComfyUI manually; this safe summary omits error and traceback text."],
        "cancelled": [
            "Confirm the cancellation was expected before any separately confirmed retry."
        ],
    }[status]


def _error_result(
    *,
    job_id: str,
    connected: bool,
    decision: str,
    error_code: str,
    warning: str,
    network_access: bool,
) -> dict[str, Any]:
    return {
        "ok": False,
        "schema_version": SCHEMA_VERSION,
        "bridge": "comfyui",
        "action": "job_snapshot",
        "endpoint": ENDPOINT_TEMPLATE,
        "mode": "live",
        "connected": connected,
        "decision": decision,
        "job": _empty_job(job_id),
        "error_code": error_code,
        "warnings": [warning],
        "redactions_applied": True,
        "safety": _safety(network_access=network_access),
        "next_steps": [
            "Check the explicit job ID and local ComfyUI version without widening the loopback scope."
        ],
    }


def build_job_snapshot(
    *,
    job_id: str,
    probe: bool = False,
    comfy_url: str = DEFAULT_COMFY_URL,
    timeout: int = 5,
    fetcher: JobFetcher | None = None,
) -> dict[str, Any]:
    if type(probe) is not bool:
        raise ValueError("probe must be boolean")
    if type(timeout) is not int or not 1 <= timeout <= 15:
        raise ValueError("timeout must be an integer between 1 and 15")
    safe_job_id = _validate_job_id(job_id)
    base_url = _validate_loopback_url(comfy_url)

    if not probe:
        return _finalize(
            {
                "ok": True,
                "schema_version": SCHEMA_VERSION,
                "bridge": "comfyui",
                "action": "job_snapshot",
                "endpoint": ENDPOINT_TEMPLATE,
                "mode": "planned",
                "connected": False,
                "decision": "planned",
                "job": _empty_job(safe_job_id),
                "error_code": None,
                "warnings": ["live_job_not_probed"],
                "redactions_applied": True,
                "safety": _safety(network_access=False),
                "next_steps": [
                    "Call again with probe=true for one direct loopback single-job status read."
                ],
            }
        )

    try:
        raw_payload = (fetcher or _read_job)(base_url, safe_job_id, timeout)
        job = normalize_job_payload(raw_payload, job_id=safe_job_id)
    except JobNotFound:
        return _finalize(
            _error_result(
                job_id=safe_job_id,
                connected=True,
                decision="not_found",
                error_code="job_not_found",
                warning="job_not_found",
                network_access=True,
            )
        )
    except (JobPayloadInvalid, TypeError, ValueError, json.JSONDecodeError):
        return _finalize(
            _error_result(
                job_id=safe_job_id,
                connected=True,
                decision="unavailable",
                error_code="job_payload_invalid",
                warning="job_payload_rejected",
                network_access=True,
            )
        )
    except (JobEndpointUnavailable, OSError, TimeoutError):
        return _finalize(
            _error_result(
                job_id=safe_job_id,
                connected=False,
                decision="unavailable",
                error_code="job_endpoint_unavailable",
                warning="loopback_job_endpoint_unavailable",
                network_access=True,
            )
        )

    status = str(job["status"])
    return _finalize(
        {
            "ok": True,
            "schema_version": SCHEMA_VERSION,
            "bridge": "comfyui",
            "action": "job_snapshot",
            "endpoint": ENDPOINT_TEMPLATE,
            "mode": "live",
            "connected": True,
            "decision": status,
            "job": job,
            "error_code": None,
            "warnings": [],
            "redactions_applied": True,
            "safety": _safety(network_access=True),
            "next_steps": _next_steps(status),
        }
    )
