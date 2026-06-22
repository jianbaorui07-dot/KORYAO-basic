"""Core helpers for StarBridge MCP.

Exposes the safety layer: evidence manifests, job status, security redaction,
safe roots, tool registry, result schemas, and computer-use adapters.
"""

__all__ = [
    # Evidence & results
    "DEFAULT_EVIDENCE_ROOT",
    "DEFAULT_MANIFEST_FILENAME",
    "EvidenceManifest",
    "EvidenceItem",
    "ExecutionResult",
    "ValidationResult",
    "create_manifest",
    "save_manifest",
    "load_manifest",
    "ensure_evidence_path",
    "repo_relative",
    # Job & status
    "JobStatus",
    # Security & safety
    "sanitize",
    "sanitize_path",
    "redact_path",
    "redact_text",
    "safe_roots_summary",
    # Registry & schemas
    "ToolCapability",
    "CAPABILITIES",
    "capability_summary",
    "list_capabilities",
    "BRIDGE_PROFILES",
    "BRIDGE_NAME_MAP",
    "BRIDGE_ALIASES",
    "make_result",
    "validate_result",
    # Config
    "StarBridgeConfig",
    "env_summary",
    # Computer use
    "ActionPlan",
    "CodexComputerUseAdapter",
    "evaluate_safety",
]

from starbridge_mcp.core.evidence import (
    DEFAULT_EVIDENCE_ROOT,
    DEFAULT_MANIFEST_FILENAME,
    EvidenceManifest,
    EvidenceItem,
    ExecutionResult,
    ValidationResult,
    create_manifest,
    save_manifest,
    load_manifest,
    ensure_evidence_path,
    repo_relative,
)
from starbridge_mcp.core.job_status import JobStatus
from starbridge_mcp.core.security import sanitize, sanitize_path, redact_path, redact_text
from starbridge_mcp.core.safe_roots import safe_roots_summary
from starbridge_mcp.core.tool_registry import (
    ToolCapability,
    CAPABILITIES,
    capability_summary,
    list_capabilities,
    BRIDGE_PROFILES,
    BRIDGE_NAME_MAP,
    BRIDGE_ALIASES,
)
from starbridge_mcp.core.result_schema import make_result, validate_result
from starbridge_mcp.core.config import StarBridgeConfig, env_summary
from starbridge_mcp.core.computer_use import (
    ActionPlan,
    CodexComputerUseAdapter,
    evaluate_safety,
)
