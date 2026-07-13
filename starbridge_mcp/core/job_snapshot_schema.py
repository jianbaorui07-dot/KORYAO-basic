from __future__ import annotations

from typing import Any

SCHEMA_VERSION = "starbridge.job-snapshot.v1"
SNAPSHOT_ID_PATTERN = r"^jobstatus_[0-9a-f]{12}$"
LOGICAL_JOB_ID_PATTERN = r"^job_[0-9a-f]{12}$"
JOB_ID_PATTERN = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
MAX_OUTPUTS_COUNT = 1_000_000
JOB_STATUSES = ("pending", "in_progress", "completed", "failed", "cancelled")
DECISIONS = ("planned", "unavailable", "not_found", *JOB_STATUSES)

JOB_SNAPSHOT_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "job_id": {
            "type": "string",
            "pattern": JOB_ID_PATTERN,
            "description": "ComfyUI 返回的 canonical lowercase UUID；只用于单任务查询，不会原样返回。",
        },
        "probe": {
            "type": "boolean",
            "default": False,
            "description": "显式允许一次只读 loopback GET；默认只返回查询计划。",
        },
        "comfy_url": {
            "type": "string",
            "maxLength": 128,
            "default": "http://127.0.0.1:8188",
            "description": "只允许无账号、query、fragment 或额外路径的 loopback HTTP URL。",
        },
        "timeout": {"type": "integer", "minimum": 1, "maximum": 15, "default": 5},
    },
    "required": ["job_id"],
    "additionalProperties": False,
}

JOB_SUMMARY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "logical_job_id": {"type": "string", "pattern": LOGICAL_JOB_ID_PATTERN},
        "status": {"type": ["string", "null"], "enum": [None, *JOB_STATUSES]},
        "terminal": {"type": "boolean"},
        "completion_ready": {"type": "boolean"},
        "outputs_count": {
            "type": ["integer", "null"],
            "minimum": 0,
            "maximum": MAX_OUTPUTS_COUNT,
        },
    },
    "required": [
        "logical_job_id",
        "status",
        "terminal",
        "completion_ready",
        "outputs_count",
    ],
    "additionalProperties": False,
}
SAFETY_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        field: {"type": "boolean"}
        for field in (
            "network_access",
            "loopback_only",
            "proxy_used",
            "redirects_followed",
            "single_job_only",
            "raw_job_ids_returned",
            "workflow_payloads_returned",
            "output_payloads_returned",
            "preview_payloads_returned",
            "error_details_returned",
            "raw_payload_retained",
            "history_endpoint_read",
            "job_mutation",
            "local_file_reads",
            "local_file_writes",
            "desktop_software_started",
        )
    },
    "required": [
        "network_access",
        "loopback_only",
        "proxy_used",
        "redirects_followed",
        "single_job_only",
        "raw_job_ids_returned",
        "workflow_payloads_returned",
        "output_payloads_returned",
        "preview_payloads_returned",
        "error_details_returned",
        "raw_payload_retained",
        "history_endpoint_read",
        "job_mutation",
        "local_file_reads",
        "local_file_writes",
        "desktop_software_started",
    ],
    "additionalProperties": False,
}

JOB_SNAPSHOT_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "ok": {"type": "boolean"},
        "schema_version": {"type": "string", "const": SCHEMA_VERSION},
        "snapshot_id": {"type": "string", "pattern": SNAPSHOT_ID_PATTERN},
        "bridge": {"type": "string", "const": "comfyui"},
        "action": {"type": "string", "const": "job_snapshot"},
        "mode": {"type": "string", "enum": ["planned", "live"]},
        "connected": {"type": "boolean"},
        "decision": {"type": "string", "enum": list(DECISIONS)},
        "endpoint": {"type": "string", "const": "/api/jobs/{job_id}"},
        "job": JOB_SUMMARY_SCHEMA,
        "error_code": {
            "type": ["string", "null"],
            "enum": [
                None,
                "job_endpoint_unavailable",
                "job_not_found",
                "job_payload_invalid",
            ],
        },
        "warnings": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": [
                    "live_job_not_probed",
                    "loopback_job_endpoint_unavailable",
                    "job_not_found",
                    "job_payload_rejected",
                ],
            },
        },
        "redactions_applied": {"type": "boolean"},
        "safety": SAFETY_OUTPUT_SCHEMA,
        "next_steps": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "ok",
        "schema_version",
        "snapshot_id",
        "bridge",
        "action",
        "mode",
        "connected",
        "decision",
        "endpoint",
        "job",
        "error_code",
        "warnings",
        "redactions_applied",
        "safety",
        "next_steps",
    ],
    "additionalProperties": False,
}
