from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from starbridge_mcp.vectorization.svg_render import render_verified_svg
from starbridge_mcp.vectorization.vector60.candidate_matrix import (
    FALLBACK_ARTIFACT,
    MAX_CANDIDATES,
    CandidateConfig,
    CandidateMatrix,
    CandidateMatrixError,
    build_candidate_matrix,
)
from starbridge_mcp.vectorization.vector60.scorer import (
    CandidateScore,
    ComplexityMetrics,
    FinalRenderEvidence,
    QualityGates,
    ScoringEvidenceError,
    VisualMetrics,
    pareto_frontier,
    score_candidate,
    score_final_svg_candidate,
    select_pareto_candidate,
)


class CandidateMatrixTests(unittest.TestCase):
    def test_every_scene_is_deterministic_auditable_and_within_the_hard_limit(self) -> None:
        for scene in ("logo", "lineart", "flat", "illustration", "unsupported_photo"):
            with self.subTest(scene=scene):
                first = build_candidate_matrix(scene)
                second = build_candidate_matrix(scene)
                self.assertEqual(first, second)
                self.assertLessEqual(len(first.candidates), MAX_CANDIDATES)
                self.assertEqual(first.candidates[0].candidate_id, "artisan_baseline")
                self.assertTrue(first.candidates[0].is_fallback)
                self.assertEqual(
                    dict(first.candidates[0].parameters)["artifact"], FALLBACK_ARTIFACT
                )
                self.assertEqual(first.audit_dict()["candidate_count"], len(first.candidates))
                for candidate in first.candidates:
                    keys = list(candidate.audit_dict()["parameters"])
                    self.assertEqual(keys, sorted(keys))

    def test_unsupported_photo_cannot_claim_vector60_candidates(self) -> None:
        matrix = build_candidate_matrix("unsupported_photo")
        self.assertEqual([item.candidate_id for item in matrix.candidates], ["artisan_baseline"])

        extra = CandidateConfig.create("extra", "vtracer", "unsupported_photo")
        with self.assertRaisesRegex(CandidateMatrixError, "only retain"):
            CandidateMatrix("unsupported_photo", (*matrix.candidates, extra))

    def test_limits_duplicate_ids_and_unsorted_parameters_are_rejected(self) -> None:
        baseline = CandidateConfig.create("artisan_baseline", "artisan", "logo", is_fallback=True)
        with self.assertRaisesRegex(CandidateMatrixError, "cannot exceed"):
            CandidateMatrix("logo", (baseline,) + tuple([baseline] * MAX_CANDIDATES))
        duplicate = CandidateConfig.create("artisan_baseline", "vtracer", "logo")
        with self.assertRaisesRegex(CandidateMatrixError, "unique"):
            CandidateMatrix("logo", (baseline, duplicate))
        with self.assertRaisesRegex(CandidateMatrixError, "sorted"):
            CandidateConfig("bad", "vtracer", "logo", (("z", 1), ("a", 2)))
        with self.assertRaisesRegex(CandidateMatrixError, "between 1 and 12"):
            build_candidate_matrix("logo", limit=13)


def _evidence(identifier: str = "a", *, elapsed_resolution: int = 32) -> FinalRenderEvidence:
    digest = hashlib.sha256(identifier.encode("utf-8")).hexdigest()
    return FinalRenderEvidence(
        renderer="test-renderer",
        svg_sha256=digest,
        render_sha256="f" * 64,
        original_width=elapsed_resolution,
        original_height=elapsed_resolution,
        render_width=elapsed_resolution,
        render_height=elapsed_resolution,
        rendered_at_original_resolution=True,
    )


def _score(
    identifier: str,
    *,
    ssim: float,
    mae: float,
    edge: float,
    anchors: int,
    elapsed: float,
    subpaths: int = 1,
    size: int = 200,
) -> CandidateScore:
    return score_candidate(
        candidate_id=identifier,
        visual=VisualMetrics(ssim, mae, edge),
        complexity=ComplexityMetrics(anchors, subpaths, size),
        elapsed_seconds=elapsed,
        evidence=_evidence(identifier),
    )


class ScoringContractTests(unittest.TestCase):
    def test_original_resolution_flag_and_final_render_kind_are_hard_gates(self) -> None:
        common = {
            "renderer": "renderer",
            "svg_sha256": "a" * 64,
            "render_sha256": "b" * 64,
            "original_width": 100,
            "original_height": 80,
            "render_width": 100,
            "render_height": 80,
        }
        with self.assertRaisesRegex(ScoringEvidenceError, "requires"):
            FinalRenderEvidence(**common, rendered_at_original_resolution=False)
        with self.assertRaisesRegex(ScoringEvidenceError, "Preview"):
            FinalRenderEvidence(
                **common,
                rendered_at_original_resolution=True,
                render_kind="preview",
            )
        with self.assertRaisesRegex(ScoringEvidenceError, "original resolution"):
            FinalRenderEvidence(
                **{**common, "render_width": 50},
                rendered_at_original_resolution=True,
            )

    def test_pareto_uses_quality_complexity_size_and_elapsed_dimensions(self) -> None:
        quality = _score("quality", ssim=0.99, mae=0.01, edge=0.99, anchors=12, elapsed=2.0)
        compact = _score("compact", ssim=0.96, mae=0.04, edge=0.95, anchors=6, elapsed=1.0)
        dominated = _score("dominated", ssim=0.95, mae=0.05, edge=0.94, anchors=12, elapsed=3.0)
        slow_clone = _score("slow", ssim=0.96, mae=0.04, edge=0.95, anchors=6, elapsed=2.0)
        larger_clone = _score(
            "large",
            ssim=0.96,
            mae=0.04,
            edge=0.95,
            anchors=6,
            elapsed=1.0,
            subpaths=2,
            size=300,
        )
        self.assertEqual(
            [
                score.candidate_id
                for score in pareto_frontier(
                    [quality, compact, dominated, slow_clone, larger_clone]
                )
            ],
            ["compact", "quality"],
        )
        self.assertIs(
            select_pareto_candidate([compact, quality, dominated], gates=QualityGates()),
            quality,
        )
        self.assertEqual(
            set(quality.audit_dict()["final_render_metrics"]),
            {"ssim", "normalized_mae", "edge_dice"},
        )
        self.assertEqual(
            set(quality.audit_dict()["vector"]),
            {"anchors", "subpaths", "bytes"},
        )

    def test_selection_returns_none_when_no_candidate_passes_quality_gates(self) -> None:
        failed = _score("failed", ssim=0.8, mae=0.2, edge=0.7, anchors=1, elapsed=0.1)
        self.assertIsNone(select_pareto_candidate([failed]))


class FinalRenderScoringTests(unittest.TestCase):
    def test_formal_scoring_performs_safe_svg_render_at_original_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            svg = root / "candidate.svg"
            svg.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="24" '
                'viewBox="0 0 32 24"><path fill="#336699" fill-rule="evenodd" stroke="none" '
                'd="M 2 2 L 30 2 L 30 22 L 2 22 Z"/></svg>',
                encoding="utf-8",
            )
            reference_path = root / "reference.png"
            render_verified_svg(
                svg,
                reference_path,
                expected_width=32,
                expected_height=24,
            )
            with Image.open(reference_path) as opened:
                reference = opened.convert("RGBA")
            score = score_final_svg_candidate(
                candidate_id="candidate",
                reference=reference,
                svg_path=svg,
                render_path=root / "final.png",
                expected_svg_width=32,
                expected_svg_height=24,
            )
            self.assertTrue(score.evidence.rendered_at_original_resolution)
            self.assertEqual(
                (score.evidence.render_width, score.evidence.render_height), reference.size
            )
            self.assertEqual(score.visual.ssim, 1.0)
            self.assertEqual(score.visual.normalized_mae, 0.0)
            self.assertEqual(score.visual.edge_dice, 1.0)
            self.assertGreater(score.complexity.anchors, 0)
            self.assertGreater(score.complexity.bytes, 0)


if __name__ == "__main__":
    unittest.main()
