"""StarBridge MCP read-only resources.

Following the MCP convention "resources describe what the client should know,
tools describe what the client can do", this module exposes static, sanitized
context (capability matrix, safe roots, bridge profiles, and the safety policy)
as MCP resources. Every resource is read-only, application-controlled, network
free, and free of private paths.
"""

from __future__ import annotations

import json
from typing import Any

from starbridge_mcp.core.safe_roots import safe_roots_summary
from starbridge_mcp.core.security import sanitize
from starbridge_mcp.core.tool_registry import BRIDGE_PROFILES, capability_summary

JsonObject = dict[str, Any]

# Short guidance returned in the MCP `initialize` result. Mature MCP servers use
# the optional `instructions` field to teach the client how to use the server
# safely before it issues any tool call.
SERVER_INSTRUCTIONS = (
    "StarBridge bridges AI agents to local creative software (ComfyUI, Blender, "
    "AutoCAD/DXF, Photoshop, Illustrator, CapCut/Jianying) on a Windows-first, "
    "local-first, safe-by-default basis.\n\n"
    "Read the `starbridge://safety-policy` resource first. Read-only probe, "
    "validate, and plan tools are safe to call directly. Tools that write or "
    "export default to dry_run and refuse real I/O until an explicit confirmation "
    "flag (confirm_write / confirm_export / confirm_run) is set, and writes stay "
    "inside declared sandbox roots. Use `starbridge.tools` to discover "
    "capabilities and their risk levels, `starbridge.safe_roots` for output "
    "boundaries, and `starbridge.status` for live readiness. The server never "
    "opens private assets, logs in, pays, or bypasses licensing."
)

SAFETY_POLICY_MARKDOWN = """# StarBridge Safety Policy

StarBridge is local-first and safe-by-default. Read this before calling any tool
that writes or launches local software.

## Default posture
- Read-only probe / validate / plan tools are safe to call directly.
- Any tool that writes, exports, or runs local software defaults to
  `dry_run=true` and performs no real I/O until confirmed.

## Confirming real actions
- Real local actions require an explicit confirmation flag matching the tool:
  `confirm_write=true`, `confirm_export=true`, or `confirm_run=true`.
- Without the matching confirmation, guarded tools return `ok=false` and refuse.

## Output boundaries
- Writes must stay inside declared sandbox / ignored output roots. See the
  `starbridge://safe-roots` resource for the exact list.
- Never open or export private PSD / AI / DWG / .blend / draft / model / customer
  asset paths through public tools.

## Discovery
- Call `starbridge.tools` to enumerate capabilities with risk levels.
- Read `starbridge://capabilities` and `starbridge://bridges` for static context.
- Call `starbridge.status` or `*.environment_probe` for live readiness.

## Out of scope by design
- No automatic login, account creation, password / OTP / token entry.
- No payments, subscriptions, or purchases.
- No uploading customer assets or private projects.
- No bypassing captchas, paywalls, licensing, or security checks.
"""


def _bridge_profiles_payload() -> JsonObject:
    return sanitize(
        {
            "ok": True,
            "framework": "StarBridge",
            "resource": "bridges",
            "bridge_count": len(BRIDGE_PROFILES),
            "bridges": {name: dict(profile) for name, profile in BRIDGE_PROFILES.items()},
        }
    )


def _json_text(payload: JsonObject) -> str:
    return json.dumps(sanitize(payload), ensure_ascii=False, indent=2)


# Each entry: (uri, name, title, description, mimeType, reader -> text).
_RESOURCE_TABLE: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "starbridge://capabilities",
        "starbridge-capabilities",
        "StarBridge Capability Matrix",
        "Full StarBridge tool capability registry with risk level, maturity, and "
        "confirmation metadata. Read-only.",
        "application/json",
    ),
    (
        "starbridge://safe-roots",
        "starbridge-safe-roots",
        "StarBridge Safe Roots",
        "Repo-relative read-only and writable sandbox roots, write policy, and MCP "
        "roots alignment hints. Read-only.",
        "application/json",
    ),
    (
        "starbridge://bridges",
        "starbridge-bridges",
        "StarBridge Bridge Profiles",
        "Static per-bridge metadata: target software, probe type, required env "
        "vars, readiness condition, and safety boundary. Read-only.",
        "application/json",
    ),
    (
        "starbridge://safety-policy",
        "starbridge-safety-policy",
        "StarBridge Safety Policy",
        "The safe-by-default protocol: dry-run defaults, confirmation flags, output "
        "boundaries, and out-of-scope actions. Read-only.",
        "text/markdown",
    ),
)


def _read_capabilities() -> tuple[str, str]:
    return "application/json", _json_text(capability_summary(bridge="all", include_guarded=True))


def _read_safe_roots() -> tuple[str, str]:
    return "application/json", _json_text(safe_roots_summary(bridge="all"))


def _read_bridges() -> tuple[str, str]:
    return "application/json", _json_text(_bridge_profiles_payload())


def _read_safety_policy() -> tuple[str, str]:
    return "text/markdown", SAFETY_POLICY_MARKDOWN


_RESOURCE_READERS = {
    "starbridge://capabilities": _read_capabilities,
    "starbridge://safe-roots": _read_safe_roots,
    "starbridge://bridges": _read_bridges,
    "starbridge://safety-policy": _read_safety_policy,
}


def list_resources() -> list[JsonObject]:
    """Return the MCP resources/list payload entries."""
    return [
        {
            "uri": uri,
            "name": name,
            "title": title,
            "description": description,
            "mimeType": mime_type,
        }
        for (uri, name, title, description, mime_type) in _RESOURCE_TABLE
    ]


def read_resource(uri: str) -> JsonObject | None:
    """Return a single MCP resources/read content entry, or None if unknown."""
    reader = _RESOURCE_READERS.get(uri)
    if reader is None:
        return None
    mime_type, text = reader()
    return {"uri": uri, "mimeType": mime_type, "text": text}
