from __future__ import annotations

import hashlib
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from PIL import Image


class ScoringEvidenceError(ValueError):
    """Raised when a candidate lacks admissible final-render evidence."""


@dataclass(frozen=True)
class FinalRenderEvidence:
    renderer: str
    svg_sha256: str
    render_sha256: str
    original_width: int
    original_height: int
    render_width: int
    render_height: int
    rendered_at_original_resolution: bool
    render_kind: str = "final_svg"

    def __post_init__(self) -> None:
        if self.render_kind != "final_svg":
            raise ScoringEvidenceError("Preview renders cannot be used as formal quality evidence.")
        if self.rendered_at_original_resolution is not True:
            raise ScoringEvidenceError(
                "Formal scoring requires rendered_at_original_resolution=true."
            )
        if (
            min(
                self.original_width,
                self.original_height,
                self.render_width,
                self.render_height,
            )
            <= 0
        ):
            raise ScoringEvidenceError("Render evidence dimensions must be positive.")
        if (self.render_width, self.render_height) != (
            self.original_width,
            self.original_height,
        ):
            raise ScoringEvidenceError("The final SVG render must match the original resolution.")
        if not self.renderer:
            raise ScoringEvidenceError("Final render evidence must identify its renderer.")
        for label, value in (
            ("svg_sha256", self.svg_sha256),
            ("render_sha256", self.render_sha256),
        ):
            if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
                raise ScoringEvidenceError(f"{label} must be a lowercase SHA-256 digest.")


@dataclass(frozen=True)
class VisualMetrics:
    ssim: float
    normalized_mae: float
    edge_dice: float

    def __post_init__(self) -> None:
        values = (self.ssim, self.normalized_mae, self.edge_dice)
        if not all(math.isfinite(value) for value in values):
            raise ValueError("Visual metrics must be finite.")
        if not -1.0 <= self.ssim <= 1.0:
            raise ValueError("SSIM must be between -1 and 1.")
        if not 0.0 <= self.normalized_mae <= 1.0:
            raise ValueError("normalized MAE must be between 0 and 1.")
        if not 0.0 <= self.edge_dice <= 1.0:
            raise ValueError("Edge Dice must be between 0 and 1.")


@dataclass(frozen=True)
class ComplexityMetrics:
    anchors: int
    subpaths: int
    bytes: int

    def __post_init__(self) -> None:
        if min(self.anchors, self.subpaths, self.bytes) < 0:
            raise ValueError("Complexity metrics cannot be negative.")


@dataclass(frozen=True)
class QualityGates:
    maximum_normalized_mae: float = 0.08
    minimum_edge_dice: float = 0.90
    minimum_ssim: float | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.maximum_normalized_mae <= 1.0:
            raise ValueError("maximum_normalized_mae must be between 0 and 1.")
        if not 0.0 <= self.minimum_edge_dice <= 1.0:
            raise ValueError("minimum_edge_dice must be between 0 and 1.")
        if self.minimum_ssim is not None and not -1.0 <= self.minimum_ssim <= 1.0:
            raise ValueError("minimum_ssim must be between -1 and 1.")


@dataclass(frozen=True)
class CandidateScore:
    candidate_id: str
    visual: VisualMetrics
    complexity: ComplexityMetrics
    elapsed_seconds: float
    evidence: FinalRenderEvidence

    def __post_init__(self) -> None:
        if not self.candidate_id:
            raise ValueError("candidate_id cannot be empty.")
        if not math.isfinite(self.elapsed_seconds) or self.elapsed_seconds < 0:
            raise ValueError("elapsed_seconds must be finite and non-negative.")

    def passes(self, gates: QualityGates) -> bool:
        return (
            self.visual.normalized_mae <= gates.maximum_normalized_mae
            and self.visual.edge_dice >= gates.minimum_edge_dice
            and (gates.minimum_ssim is None or self.visual.ssim >= gates.minimum_ssim)
        )

    def audit_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "final_render_metrics": {
                "ssim": self.visual.ssim,
                "normalized_mae": self.visual.normalized_mae,
                "edge_dice": self.visual.edge_dice,
            },
            "vector": {
                "anchors": self.complexity.anchors,
                "subpaths": self.complexity.subpaths,
                "bytes": self.complexity.bytes,
            },
            "elapsed_seconds": self.elapsed_seconds,
            "render_evidence": {
                "renderer": self.evidence.renderer,
                "svg_sha256": self.evidence.svg_sha256,
                "render_sha256": self.evidence.render_sha256,
                "render_kind": self.evidence.render_kind,
                "original_resolution": [
                    self.evidence.original_width,
                    self.evidence.original_height,
                ],
                "render_resolution": [
                    self.evidence.render_width,
                    self.evidence.render_height,
                ],
                "rendered_at_original_resolution": (self.evidence.rendered_at_original_resolution),
            },
        }


def score_candidate(
    *,
    candidate_id: str,
    visual: VisualMetrics,
    complexity: ComplexityMetrics,
    elapsed_seconds: float,
    evidence: FinalRenderEvidence,
) -> CandidateScore:
    """Admit already measured metrics only when final-resolution evidence is valid."""
    return CandidateScore(candidate_id, visual, complexity, elapsed_seconds, evidence)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def score_final_svg_candidate(
    *,
    candidate_id: str,
    reference: Image.Image,
    svg_path: Path,
    render_path: Path,
    expected_svg_width: int,
    expected_svg_height: int,
    detail_protection: float = 0.75,
    supersample: int = 2,
) -> CandidateScore:
    """Safely render an SVG at the source resolution and create its formal score."""
    from PIL import Image as PillowImage

    from ..adaptive_optimize import _composite_white, _quality_metrics
    from ..svg_render import render_verified_svg
    from ..svg_verify import verify_svg_artifact

    started = time.perf_counter()
    artifact = verify_svg_artifact(
        svg_path,
        expected_width=expected_svg_width,
        expected_height=expected_svg_height,
    )
    render_result = render_verified_svg(
        svg_path,
        render_path,
        expected_width=expected_svg_width,
        expected_height=expected_svg_height,
        supersample=supersample,
        output_width=reference.width,
        output_height=reference.height,
    )
    with PillowImage.open(render_path) as opened:
        rendered = opened.convert("RGBA")
    if rendered.size != reference.size:
        raise ScoringEvidenceError("Renderer output does not match the original resolution.")

    reference_rgb, reference_alpha = _composite_white(reference)
    rendered_rgb, rendered_alpha = _composite_white(rendered)
    measured = _quality_metrics(
        reference_rgb,
        rendered_rgb,
        reference_alpha,
        rendered_alpha,
        detail_protection,
    )
    evidence = FinalRenderEvidence(
        renderer=str(render_result["renderer"]),
        svg_sha256=str(artifact["sha256"]),
        render_sha256=_sha256(render_path),
        original_width=reference.width,
        original_height=reference.height,
        render_width=rendered.width,
        render_height=rendered.height,
        rendered_at_original_resolution=True,
    )
    return score_candidate(
        candidate_id=candidate_id,
        visual=VisualMetrics(
            ssim=float(measured["ssim"]),
            normalized_mae=float(measured["normalized_mae"]),
            edge_dice=float(measured["edge_dice"]),
        ),
        complexity=ComplexityMetrics(
            anchors=int(artifact["anchor_point_count"]),
            subpaths=int(artifact["subpath_count"]),
            bytes=int(artifact["bytes"]),
        ),
        elapsed_seconds=round(time.perf_counter() - started, 6),
        evidence=evidence,
    )


def _dimensions(score: CandidateScore) -> tuple[float | int, ...]:
    return (
        1.0 - score.visual.ssim,
        score.visual.normalized_mae,
        1.0 - score.visual.edge_dice,
        score.complexity.anchors,
        score.complexity.subpaths,
        score.complexity.bytes,
        score.elapsed_seconds,
    )


def pareto_frontier(scores: list[CandidateScore]) -> list[CandidateScore]:
    """Return the deterministic non-dominated frontier across all Vector60 dimensions."""
    identifiers = [score.candidate_id for score in scores]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Candidate score identifiers must be unique.")
    frontier: list[CandidateScore] = []
    for candidate in scores:
        values = _dimensions(candidate)
        dominated = False
        for other in scores:
            if other is candidate:
                continue
            other_values = _dimensions(other)
            if all(left <= right for left, right in zip(other_values, values)) and any(
                left < right for left, right in zip(other_values, values)
            ):
                dominated = True
                break
        if not dominated:
            frontier.append(candidate)
    return sorted(frontier, key=lambda candidate: candidate.candidate_id)


def select_pareto_candidate(
    scores: list[CandidateScore],
    *,
    gates: QualityGates = QualityGates(),
) -> CandidateScore | None:
    """Select a quality-passing Pareto candidate with deterministic quality-first ties."""
    eligible = [score for score in scores if score.passes(gates)]
    if not eligible:
        return None
    frontier = pareto_frontier(eligible)
    return min(
        frontier,
        key=lambda score: (
            -score.visual.ssim,
            score.visual.normalized_mae,
            -score.visual.edge_dice,
            score.complexity.anchors,
            score.complexity.subpaths,
            score.complexity.bytes,
            score.elapsed_seconds,
            score.candidate_id,
        ),
    )
