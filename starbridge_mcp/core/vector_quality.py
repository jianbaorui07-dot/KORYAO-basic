from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from starbridge_mcp.core.security import sanitize

DIMENSION_WEIGHTS: dict[str, float] = {
    "geometry": 0.28,
    "topology": 0.24,
    "editability": 0.18,
    "visual": 0.20,
    "production": 0.10,
}
REQUIRED_HARD_GATES = (
    "reference_authorized",
    "primary_silhouette_present",
    "topology_valid",
    "editable_vector_present",
    "safe_output_scope",
)
VALID_SEVERITIES = ("info", "warn", "critical")
PASS_SCORE = 90.0
MINIMUM_DIMENSION_SCORE = 75.0


def _ensure_score(value: float, *, name: str) -> float:
    score = float(value)
    if not 0 <= score <= 100:
        raise ValueError(f"{name} score must be between 0 and 100")
    return score


@dataclass(frozen=True)
class VectorQualityFinding:
    code: str
    dimension: str
    severity: str
    message: str
    object_id: str | None = None
    suggested_patch: str | None = None

    def __post_init__(self) -> None:
        if self.dimension not in DIMENSION_WEIGHTS:
            raise ValueError(f"unknown vector quality dimension: {self.dimension}")
        if self.severity not in VALID_SEVERITIES:
            raise ValueError(f"severity must be one of {', '.join(VALID_SEVERITIES)}")
        if not self.code.strip() or not self.message.strip():
            raise ValueError("finding code and message must not be empty")

    def to_dict(self) -> dict[str, Any]:
        return sanitize(
            {
                "code": self.code,
                "dimension": self.dimension,
                "severity": self.severity,
                "message": self.message,
                "object_id": self.object_id,
                "suggested_patch": self.suggested_patch,
            }
        )


@dataclass(frozen=True)
class VectorDimensionResult:
    score: float
    checks: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _ensure_score(self.score, name="dimension")

    def to_dict(self) -> dict[str, Any]:
        return {"score": round(float(self.score), 2), "checks": list(self.checks)}


def evaluate_reference_vector_quality(
    *,
    reference_id: str,
    candidate_id: str,
    dimensions: dict[str, VectorDimensionResult],
    hard_gates: dict[str, bool],
    findings: list[VectorQualityFinding] | None = None,
) -> dict[str, Any]:
    if not reference_id.strip() or not candidate_id.strip():
        raise ValueError("reference_id and candidate_id must not be empty")
    missing_dimensions = sorted(set(DIMENSION_WEIGHTS) - set(dimensions))
    extra_dimensions = sorted(set(dimensions) - set(DIMENSION_WEIGHTS))
    if missing_dimensions or extra_dimensions:
        raise ValueError(
            "dimensions must match quality model; "
            f"missing={missing_dimensions}, extra={extra_dimensions}"
        )
    missing_gates = sorted(set(REQUIRED_HARD_GATES) - set(hard_gates))
    extra_gates = sorted(set(hard_gates) - set(REQUIRED_HARD_GATES))
    if missing_gates or extra_gates:
        raise ValueError(
            f"hard_gates must match required gates; missing={missing_gates}, extra={extra_gates}"
        )
    if not all(isinstance(value, bool) for value in hard_gates.values()):
        raise TypeError("hard gate values must be bool")

    finding_items = findings or []
    scores = {name: float(dimensions[name].score) for name in DIMENSION_WEIGHTS}
    overall_score = sum(scores[name] * DIMENSION_WEIGHTS[name] for name in DIMENSION_WEIGHTS)
    minimum_score = min(scores.values())
    critical_count = sum(1 for item in finding_items if item.severity == "critical")
    gates_ok = all(hard_gates.values())

    if not gates_ok or critical_count:
        verdict = "blocked"
    elif overall_score >= PASS_SCORE and minimum_score >= MINIMUM_DIMENSION_SCORE:
        verdict = "pass"
    else:
        verdict = "repair_needed"

    return sanitize(
        {
            "schema_version": "starbridge.reference-vector-quality.v1",
            "reference_id": reference_id,
            "candidate_id": candidate_id,
            "dimensions": {
                name: dimensions[name].to_dict() for name in DIMENSION_WEIGHTS
            },
            "hard_gates": {name: hard_gates[name] for name in REQUIRED_HARD_GATES},
            "findings": [item.to_dict() for item in finding_items],
            "overall_score": round(overall_score, 2),
            "minimum_dimension_score": round(minimum_score, 2),
            "verdict": verdict,
        }
    )


def validate_reference_vector_quality_report(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    required = {
        "schema_version",
        "reference_id",
        "candidate_id",
        "dimensions",
        "hard_gates",
        "findings",
        "overall_score",
        "minimum_dimension_score",
        "verdict",
    }
    missing = sorted(required - set(payload))
    if missing:
        return [f"missing fields: {', '.join(missing)}"]
    if payload["schema_version"] != "starbridge.reference-vector-quality.v1":
        failures.append("unsupported schema_version")
    if set(payload["dimensions"]) != set(DIMENSION_WEIGHTS):
        failures.append("dimensions do not match quality model")
    else:
        for name, item in payload["dimensions"].items():
            if not isinstance(item, dict) or "score" not in item or "checks" not in item:
                failures.append(f"invalid dimension payload: {name}")
                continue
            try:
                _ensure_score(float(item["score"]), name=name)
            except (TypeError, ValueError) as exc:
                failures.append(str(exc))
            if not isinstance(item["checks"], list):
                failures.append(f"{name}.checks must be list")
    if set(payload["hard_gates"]) != set(REQUIRED_HARD_GATES):
        failures.append("hard_gates do not match required gates")
    elif not all(isinstance(value, bool) for value in payload["hard_gates"].values()):
        failures.append("hard gate values must be bool")
    if not isinstance(payload["findings"], list):
        failures.append("findings must be list")
    if payload["verdict"] not in {"pass", "repair_needed", "blocked"}:
        failures.append("invalid verdict")
    return failures
