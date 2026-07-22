from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

MAX_CANDIDATES = 12
FALLBACK_ARTIFACT = "artisan_baseline.svg"
SUPPORTED_SCENES = frozenset({"logo", "lineart", "flat", "illustration", "unsupported_photo"})

AuditValue = str | int | float | bool | None


class CandidateMatrixError(ValueError):
    """Raised when a candidate matrix cannot be safely or deterministically audited."""


@dataclass(frozen=True)
class CandidateConfig:
    """One immutable, audit-friendly vectorization candidate configuration."""

    candidate_id: str
    backend: str
    scene_preset: str
    parameters: tuple[tuple[str, AuditValue], ...] = ()
    is_fallback: bool = False

    def __post_init__(self) -> None:
        if not self.candidate_id or not all(
            character.isalnum() or character in {"_", "-"} for character in self.candidate_id
        ):
            raise CandidateMatrixError(
                "candidate_id must contain only letters, digits, '_' or '-'."
            )
        if not self.backend or not all(
            character.isalnum() or character in {"_", "-"} for character in self.backend
        ):
            raise CandidateMatrixError("backend must contain only letters, digits, '_' or '-'.")
        if self.scene_preset not in SUPPORTED_SCENES:
            raise CandidateMatrixError(f"Unsupported scene preset: {self.scene_preset}")
        keys = [key for key, _ in self.parameters]
        if keys != sorted(keys) or len(keys) != len(set(keys)):
            raise CandidateMatrixError("Candidate parameters must have unique, sorted keys.")
        for key, value in self.parameters:
            if not key:
                raise CandidateMatrixError("Candidate parameter names cannot be empty.")
            if not isinstance(value, (str, int, float, bool, type(None))):
                raise CandidateMatrixError(f"Candidate parameter {key!r} is not audit-safe.")
            if isinstance(value, float) and not math.isfinite(value):
                raise CandidateMatrixError(f"Candidate parameter {key!r} must be finite.")

    @classmethod
    def create(
        cls,
        candidate_id: str,
        backend: str,
        scene_preset: str,
        *,
        parameters: dict[str, AuditValue] | None = None,
        is_fallback: bool = False,
    ) -> CandidateConfig:
        return cls(
            candidate_id=candidate_id,
            backend=backend,
            scene_preset=scene_preset,
            parameters=tuple(sorted((parameters or {}).items())),
            is_fallback=is_fallback,
        )

    def audit_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "backend": self.backend,
            "scene_preset": self.scene_preset,
            "parameters": dict(self.parameters),
            "is_fallback": self.is_fallback,
        }


@dataclass(frozen=True)
class CandidateMatrix:
    scene_preset: str
    candidates: tuple[CandidateConfig, ...]

    def __post_init__(self) -> None:
        if self.scene_preset not in SUPPORTED_SCENES:
            raise CandidateMatrixError(f"Unsupported scene preset: {self.scene_preset}")
        if not self.candidates:
            raise CandidateMatrixError("A candidate matrix must contain the artisan baseline.")
        if len(self.candidates) > MAX_CANDIDATES:
            raise CandidateMatrixError(f"Candidate count cannot exceed {MAX_CANDIDATES}.")
        identifiers = [candidate.candidate_id for candidate in self.candidates]
        if len(identifiers) != len(set(identifiers)):
            raise CandidateMatrixError("Candidate identifiers must be unique.")
        if any(candidate.scene_preset != self.scene_preset for candidate in self.candidates):
            raise CandidateMatrixError("Every candidate must use the matrix scene preset.")
        fallbacks = [candidate for candidate in self.candidates if candidate.is_fallback]
        if len(fallbacks) != 1 or not self.candidates[0].is_fallback:
            raise CandidateMatrixError("Exactly one fallback is required and it must be first.")
        if self.candidates[0].candidate_id != "artisan_baseline":
            raise CandidateMatrixError("The fallback candidate must be artisan_baseline.")
        if self.scene_preset == "unsupported_photo" and len(self.candidates) != 1:
            raise CandidateMatrixError("Unsupported photos may only retain the existing fallback.")

    def audit_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "scene_preset": self.scene_preset,
            "candidate_count": len(self.candidates),
            "maximum_candidates": MAX_CANDIDATES,
            "candidates": [candidate.audit_dict() for candidate in self.candidates],
        }


def _candidate(
    candidate_id: str,
    scene_preset: str,
    **parameters: AuditValue,
) -> CandidateConfig:
    return CandidateConfig.create(
        candidate_id,
        "vtracer",
        scene_preset,
        parameters=parameters,
    )


def _scene_candidates(scene_preset: str) -> tuple[CandidateConfig, ...]:
    baseline = CandidateConfig.create(
        "artisan_baseline",
        "artisan",
        scene_preset,
        parameters={
            "artifact": FALLBACK_ARTIFACT,
            "source": "existing_artisan_baseline",
        },
        is_fallback=True,
    )
    if scene_preset == "unsupported_photo":
        return (baseline,)

    common = (
        _candidate(
            "vtracer_balanced",
            scene_preset,
            color_precision=6,
            filter_speckle=4,
            hierarchical="stacked",
            mode="spline",
            path_precision=3,
        ),
        _candidate(
            "vtracer_cutout",
            scene_preset,
            color_precision=6,
            filter_speckle=4,
            hierarchical="cutout",
            mode="spline",
            path_precision=3,
        ),
    )
    if scene_preset == "logo":
        specialized = (
            _candidate(
                "vtracer_logo_crisp",
                scene_preset,
                color_precision=8,
                corner_threshold=45,
                filter_speckle=2,
                hierarchical="cutout",
                mode="polygon",
                path_precision=4,
            ),
            _candidate(
                "vtracer_logo_smooth",
                scene_preset,
                color_precision=8,
                filter_speckle=2,
                hierarchical="stacked",
                length_threshold=3.5,
                mode="spline",
                path_precision=4,
            ),
        )
    elif scene_preset == "lineart":
        specialized = (
            _candidate(
                "vtracer_lineart_fine",
                scene_preset,
                colormode="binary",
                filter_speckle=1,
                hierarchical="cutout",
                length_threshold=2.5,
                mode="spline",
                path_precision=4,
            ),
            _candidate(
                "vtracer_lineart_polygon",
                scene_preset,
                colormode="binary",
                corner_threshold=50,
                filter_speckle=1,
                hierarchical="cutout",
                mode="polygon",
                path_precision=4,
            ),
        )
    elif scene_preset == "flat":
        specialized = (
            _candidate(
                "vtracer_flat_precise",
                scene_preset,
                color_precision=8,
                filter_speckle=3,
                hierarchical="cutout",
                layer_difference=8,
                mode="spline",
                path_precision=4,
            ),
            _candidate(
                "vtracer_flat_compact",
                scene_preset,
                color_precision=5,
                filter_speckle=6,
                hierarchical="stacked",
                layer_difference=16,
                mode="spline",
                path_precision=3,
            ),
        )
    else:
        specialized = (
            _candidate(
                "vtracer_illustration_detail",
                scene_preset,
                color_precision=7,
                filter_speckle=2,
                hierarchical="stacked",
                layer_difference=8,
                mode="spline",
                path_precision=4,
            ),
            _candidate(
                "vtracer_illustration_compact",
                scene_preset,
                color_precision=5,
                filter_speckle=8,
                hierarchical="stacked",
                layer_difference=16,
                mode="spline",
                path_precision=3,
            ),
        )
    return (baseline, *common, *specialized)


def build_candidate_matrix(
    scene_preset: str,
    *,
    limit: int = MAX_CANDIDATES,
) -> CandidateMatrix:
    """Build the deterministic Vector60 matrix, always retaining the fallback first."""
    if not 1 <= limit <= MAX_CANDIDATES:
        raise CandidateMatrixError(f"limit must be between 1 and {MAX_CANDIDATES}.")
    candidates = _scene_candidates(scene_preset)
    return CandidateMatrix(scene_preset, candidates[:limit])
