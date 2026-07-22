from __future__ import annotations

import math
import unittest

from starbridge_mcp.vectorization.vector60.primitive_fit import (
    FinalRenderEvidence,
    PrimitiveFitLimits,
    PrimitiveKind,
    PrimitiveProposal,
    TopologySignature,
    apply_primitive_fit,
)
from starbridge_mcp.vectorization.vector60.seam_repair import (
    MAXIMUM_SAFE_OVERLAP_PX,
    MAXIMUM_VERTEX_SNAP_PX,
    RegionSnapshot,
    RenderMetrics,
    RepairCandidate,
    RepairRenderEvidence,
    SeamOperation,
    SeamRepairProposal,
    apply_seam_repair,
    color_delta_e,
)

CLOSED = TopologySignature(True, 1, 0, (None,), (1,))
OPEN = TopologySignature(False, 1, 0, (None,), (1,))


class PrimitiveFitTests(unittest.TestCase):
    def _proposal(
        self,
        kind: PrimitiveKind | str = PrimitiveKind.RECTANGLE,
        *,
        topology: TopologySignature = CLOSED,
        contour_error: float = 0.2,
        area_error: float = 0.005,
        path_data: str = "M 1 1 L 9 1 L 9 9 L 1 9 Z",
    ) -> PrimitiveProposal:
        if kind is PrimitiveKind.LINE and path_data.endswith(" Z"):
            path_data = path_data[:-2]
        return PrimitiveProposal(kind, path_data, contour_error, area_error, topology)

    @staticmethod
    def _render_gate(_: str) -> FinalRenderEvidence:
        return FinalRenderEvidence(10, 10, 10, 10, True)

    def test_all_supported_primitives_can_pass_the_complete_gate(self) -> None:
        for kind in PrimitiveKind:
            topology = OPEN if kind is PrimitiveKind.LINE else CLOSED
            proposal = self._proposal(kind, topology=topology)
            result = apply_primitive_fit(
                original_path_data="M 0 0 L 10 0 L 10 10 L 0 10 Z",
                original_topology=topology,
                proposal=proposal,
                render_gate=self._render_gate,
            )
            with self.subTest(kind=kind):
                self.assertTrue(result.replaced)
                self.assertEqual(result.path_data, proposal.path_data)
                self.assertTrue(all(result.gates.values()))

    def test_unsupported_primitive_is_rejected_before_render(self) -> None:
        rendered = False

        def render(_: str) -> FinalRenderEvidence:
            nonlocal rendered
            rendered = True
            return self._render_gate("")

        result = apply_primitive_fit(
            original_path_data="original",
            original_topology=CLOSED,
            proposal=self._proposal("freeform"),
            render_gate=render,
        )
        self.assertFalse(result.replaced)
        self.assertEqual(result.path_data, "original")
        self.assertFalse(rendered)
        self.assertIn("unsupported_primitive", result.rejection_reasons)

    def test_geometry_and_topology_gates_fail_closed(self) -> None:
        cases = (
            (self._proposal(contour_error=0.51), "contour_error_gate"),
            (self._proposal(area_error=0.011), "area_error_gate"),
            (
                self._proposal(topology=TopologySignature(True, 2, 1, (None, "outer"), (1, -1))),
                "topology_gate",
            ),
            (self._proposal(contour_error=math.nan), "contour_error_gate"),
            (self._proposal(path_data='<image href="remote">'), "unsafe_path_data"),
        )
        for proposal, reason in cases:
            result = apply_primitive_fit(
                original_path_data="original",
                original_topology=CLOSED,
                proposal=proposal,
                render_gate=self._render_gate,
            )
            with self.subTest(reason=reason):
                self.assertFalse(result.replaced)
                self.assertEqual(result.path_data, "original")
                self.assertIn(reason, result.rejection_reasons)

    def test_line_and_filled_shapes_enforce_open_closed_topology(self) -> None:
        for proposal in (
            self._proposal(PrimitiveKind.LINE, topology=CLOSED),
            self._proposal(PrimitiveKind.CIRCLE, topology=OPEN),
        ):
            result = apply_primitive_fit(
                original_path_data="original",
                original_topology=proposal.topology,
                proposal=proposal,
                render_gate=self._render_gate,
            )
            self.assertFalse(result.replaced)
            self.assertIn("topology_gate", result.rejection_reasons)

    def test_final_render_must_pass_at_original_resolution(self) -> None:
        evidence = (
            None,
            lambda _: FinalRenderEvidence(10, 10, 20, 20, True),
            lambda _: FinalRenderEvidence(10, 10, 10, 10, False),
        )
        for render_gate in evidence:
            result = apply_primitive_fit(
                original_path_data="original",
                original_topology=CLOSED,
                proposal=self._proposal(),
                render_gate=render_gate,
            )
            self.assertFalse(result.replaced)
            self.assertEqual(result.path_data, "original")

    def test_render_error_and_invalid_limits_retain_original(self) -> None:
        def fail(_: str) -> FinalRenderEvidence:
            raise RuntimeError("renderer failed")

        render_error = apply_primitive_fit(
            original_path_data="original",
            original_topology=CLOSED,
            proposal=self._proposal(),
            render_gate=fail,
        )
        invalid_limits = apply_primitive_fit(
            original_path_data="original",
            original_topology=CLOSED,
            proposal=self._proposal(),
            render_gate=self._render_gate,
            limits=PrimitiveFitLimits(-1, 2),
        )
        self.assertIn("final_render_error", render_error.rejection_reasons)
        self.assertFalse(invalid_limits.replaced)


class SeamRepairTests(unittest.TestCase):
    def setUp(self) -> None:
        self.regions = {
            "left": RegionSnapshot("left", "#336699", CLOSED),
            "right": RegionSnapshot("right", "#336699", CLOSED),
        }

    def _candidate(
        self,
        proposal: SeamRepairProposal,
        *,
        topologies: dict[str, TopologySignature] | None = None,
        affected: tuple[str, ...] | None = None,
    ) -> RepairCandidate:
        region_ids = tuple(dict.fromkeys(proposal.region_ids))
        if proposal.operation == SeamOperation.SAFE_OVERLAP:
            assert proposal.bottom_region_id is not None
            region_ids = (proposal.bottom_region_id,)
        return RepairCandidate(
            dict.fromkeys(region_ids, "M 0 0 L 10 0 L 10 10 L 0 10 Z"),
            topologies or {key: value.topology for key, value in self.regions.items()},
            affected or region_ids,
        )

    @staticmethod
    def _render(
        _: RepairCandidate,
        *,
        before: RenderMetrics = RenderMetrics(0.9, 0.08, 0.9),
        after: RenderMetrics = RenderMetrics(0.91, 0.07, 0.91),
        rendered_width: int = 100,
    ) -> RepairRenderEvidence:
        return RepairRenderEvidence(100, 80, rendered_width, 80, before, after)

    def _apply(self, proposal: SeamRepairProposal, **kwargs: object):
        return apply_seam_repair(
            regions=self.regions,
            proposal=proposal,
            candidate_builder=kwargs.pop("candidate_builder", self._candidate),
            render_evaluator=kwargs.pop("render_evaluator", self._render),
            **kwargs,
        )

    def test_vertex_snap_accepts_0_8_pixels_and_rejects_more(self) -> None:
        accepted = self._apply(
            SeamRepairProposal(SeamOperation.SNAP, ("left", "right"), snap_distance_px=0.8)
        )
        rejected = self._apply(
            SeamRepairProposal(
                SeamOperation.SNAP,
                ("left", "right"),
                snap_distance_px=MAXIMUM_VERTEX_SNAP_PX + 0.001,
            )
        )
        self.assertTrue(accepted.applied)
        self.assertFalse(rejected.applied)
        self.assertIn("operation_limit_gate", rejected.rejection_reasons)

    def test_union_allows_same_color_and_gates_near_color_by_delta_e(self) -> None:
        same = self._apply(SeamRepairProposal(SeamOperation.UNION, ("left", "right")))
        self.assertTrue(same.applied)
        self.assertEqual(same.delta_e, 0.0)

        self.regions["right"] = RegionSnapshot("right", "#346699", CLOSED)
        delta = color_delta_e("#336699", "#346699")
        self.assertGreater(delta, 0)
        near = self._apply(
            SeamRepairProposal(SeamOperation.UNION, ("left", "right")),
            maximum_delta_e=delta,
        )
        blocked = self._apply(
            SeamRepairProposal(SeamOperation.UNION, ("left", "right")),
            maximum_delta_e=delta / 2,
        )
        self.assertTrue(near.applied)
        self.assertFalse(blocked.applied)
        self.assertIn("color_gate", blocked.rejection_reasons)

    def test_union_checks_delta_e_for_every_color_pair(self) -> None:
        self.regions["middle"] = RegionSnapshot("middle", "#346699", CLOSED)
        self.regions["right"] = RegionSnapshot("right", "#356699", CLOSED)
        neighbor_delta = color_delta_e("#336699", "#346699")
        end_delta = color_delta_e("#336699", "#356699")
        self.assertLess(neighbor_delta, end_delta)
        result = self._apply(
            SeamRepairProposal(SeamOperation.UNION, ("left", "middle", "right")),
            maximum_delta_e=neighbor_delta,
        )
        self.assertFalse(result.applied)
        self.assertAlmostEqual(result.delta_e or 0, end_delta)

    def test_safe_overlap_is_limited_to_0_4_pixels_and_requires_bottom_region(self) -> None:
        accepted = self._apply(
            SeamRepairProposal(
                SeamOperation.SAFE_OVERLAP,
                ("left", "right"),
                overlap_px=MAXIMUM_SAFE_OVERLAP_PX,
                bottom_region_id="left",
            )
        )
        too_wide = self._apply(
            SeamRepairProposal(
                SeamOperation.SAFE_OVERLAP,
                ("left", "right"),
                overlap_px=MAXIMUM_SAFE_OVERLAP_PX + 0.001,
                bottom_region_id="left",
            )
        )
        no_bottom = self._apply(
            SeamRepairProposal(
                SeamOperation.SAFE_OVERLAP,
                ("left", "right"),
                overlap_px=0.2,
            )
        )
        self.assertTrue(accepted.applied)
        self.assertFalse(too_wide.applied)
        self.assertFalse(no_bottom.applied)

    def test_any_render_metric_regression_rolls_back(self) -> None:
        proposal = SeamRepairProposal(SeamOperation.SNAP, ("left", "right"), snap_distance_px=0.2)
        degraded = (
            RenderMetrics(0.89, 0.08, 0.9),
            RenderMetrics(0.9, 0.081, 0.9),
            RenderMetrics(0.9, 0.08, 0.89),
        )
        for after in degraded:
            result = self._apply(
                proposal,
                render_evaluator=lambda candidate, after=after: self._render(
                    candidate, after=after
                ),
            )
            with self.subTest(after=after):
                self.assertFalse(result.applied)
                self.assertIsNone(result.candidate)
                self.assertIn("metric_degraded", result.rejection_reasons)

    def test_hole_parent_or_component_topology_change_rolls_back(self) -> None:
        proposal = SeamRepairProposal(SeamOperation.SNAP, ("left", "right"), snap_distance_px=0.2)
        changed = TopologySignature(True, 2, 1, (None, "left"), (1, -1))
        result = self._apply(
            proposal,
            candidate_builder=lambda item: self._candidate(
                item, topologies={"left": changed, "right": CLOSED}
            ),
        )
        self.assertFalse(result.applied)
        self.assertIn("topology_gate", result.rejection_reasons)

    def test_global_scope_dilation_and_out_of_scope_changes_are_rejected(self) -> None:
        global_repair = self._apply(
            SeamRepairProposal(
                SeamOperation.SNAP,
                ("left", "right"),
                local=False,
                snap_distance_px=0.2,
            )
        )
        dilation = self._apply(SeamRepairProposal("dilate", ("left", "right"), overlap_px=0.2))
        out_of_scope = self._apply(
            SeamRepairProposal(SeamOperation.SNAP, ("left",), snap_distance_px=0.2),
            candidate_builder=lambda item: self._candidate(item, affected=("left", "right")),
        )
        self.assertFalse(global_repair.applied)
        self.assertFalse(dilation.applied)
        self.assertFalse(out_of_scope.applied)
        self.assertIn("unsupported_operation", dilation.rejection_reasons)

    def test_safe_overlap_may_only_modify_the_bottom_region(self) -> None:
        proposal = SeamRepairProposal(
            SeamOperation.SAFE_OVERLAP,
            ("left", "right"),
            overlap_px=0.2,
            bottom_region_id="left",
        )
        touches_top = self._apply(
            proposal,
            candidate_builder=lambda item: RepairCandidate(
                dict.fromkeys(item.region_ids, "M 0 0 L 1 0 L 1 1 Z"),
                {key: value.topology for key, value in self.regions.items()},
                item.region_ids,
            ),
        )
        self.assertFalse(touches_top.applied)
        self.assertIn("candidate_scope_gate", touches_top.rejection_reasons)

    def test_candidate_path_render_resolution_and_dependency_failures_fail_closed(self) -> None:
        proposal = SeamRepairProposal(SeamOperation.SNAP, ("left", "right"), snap_distance_px=0.2)
        unsafe = self._apply(
            proposal,
            candidate_builder=lambda item: RepairCandidate(
                {"left": "<script>alert(1)</script>", "right": "M 0 0 L 1 1"},
                {key: value.topology for key, value in self.regions.items()},
                item.region_ids,
            ),
        )
        wrong_resolution = self._apply(
            proposal,
            render_evaluator=lambda candidate: self._render(candidate, rendered_width=200),
        )

        def builder_error(_: SeamRepairProposal) -> RepairCandidate:
            raise RuntimeError("pathops unavailable")

        unavailable = self._apply(proposal, candidate_builder=builder_error)
        self.assertFalse(unsafe.applied)
        self.assertFalse(wrong_resolution.applied)
        self.assertFalse(unavailable.applied)


if __name__ == "__main__":
    unittest.main()
