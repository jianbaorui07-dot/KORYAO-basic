from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from starbridge_mcp.core.result_schema import make_result
from starbridge_mcp.core.security import sanitize_result


class BaseBridge(ABC):
    """Base class for StarBridge adapters and bridges.

    Provides common patterns for status, safety, evidence, and result handling.
    Subclasses should implement bridge_id and core actions.
    """

    @property
    @abstractmethod
    def bridge_id(self) -> str: ...

    @property
    def repo_root(self) -> Path:
        # Default, can be overridden or set in __init__
        return Path(__file__).resolve().parents[2]

    def _result(
        self,
        *,
        ok: bool,
        action: str,
        message: str,
        details: dict[str, Any] | None = None,
        warnings: list[str] | None = None,
        next_steps: list[str] | None = None,
    ) -> dict[str, Any]:
        result = make_result(
            ok=ok,
            bridge=self.bridge_id,
            action=action,
            message=message,
            details=details or {},
            warnings=warnings or [],
            next_steps=next_steps or [],
        )
        return sanitize_result(result)

    def status(self) -> dict[str, Any]:
        """Default status implementation. Override for specifics."""
        return self._result(
            ok=True,
            action="status",
            message=f"{self.bridge_id} bridge is available.",
            details={"bridge_id": self.bridge_id},
        )

    def probe(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Default probe. Most bridges override this."""
        return self._result(
            ok=True,
            action="probe",
            message="Probe not fully implemented for this bridge.",
            details={"arguments": arguments},
            warnings=["This is a base implementation."],
        )
