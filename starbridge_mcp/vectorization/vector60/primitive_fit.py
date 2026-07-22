from __future__ import annotations

import math
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import Enum


class PrimitiveKind(str, Enum):
    """Vector60 primitives that may replace an existing path."""

    LINE = "line"
    RECTANGLE = "rectangle"
    ROUNDED_RECTANGLE = "rounded_rectangle"
    CIRCLE = "circle"
    ELLIPSE = "ellipse"
    REGULAR_POLYGON = "regular_polygon"


SUPPORTED_PRIMITIVES = frozenset(PrimitiveKind)
_SAFE_PATH_DATA = re.compile(r"[MLCZ0-9eE+.\-\s]+\Z")


@dataclass(frozen=True)
class TopologySignature:
    """Topology evidence that must remain identical across a replacement."""

    closed: bool
    subpaths: int
    holes: int
    parent_ids: tuple[str | None, ...] = ()
    winding: tuple[int, ...] = ()

    def is_valid(self) -> bool:
        if (
            type(self.closed) is not bool
            or type(self.subpaths) is not int
            or type(self.holes) is not int
            or not isinstance(self.parent_ids, tuple)
            or not isinstance(self.winding, tuple)
        ):
            return False
        if self.subpaths < 1 or self.holes < 0 or self.holes >= self.subpaths:
            return False
        if len(self.parent_ids) != self.subpaths:
            return False
        if len(self.winding) != self.subpaths:
            return False
        return all(value in {-1, 1} for value in self.winding)


@dataclass(frozen=True)
class PrimitiveFitLimits:
    maximum_contour_error_px: float = 0.5
    maximum_area_error_ratio: float = 0.01

    def is_valid(self) -> bool:
        try:
            return (
                math.isfinite(self.maximum_contour_error_px)
                and self.maximum_contour_error_px >= 0
                and math.isfinite(self.maximum_area_error_ratio)
                and 0 <= self.maximum_area_error_ratio <= 1
            )
        except TypeError:
            return False


@dataclass(frozen=True)
class PrimitiveProposal:
    """A fitted path plus geometry evidence produced by a fitter.

    The fitter may use svgpathtools or another audited implementation. This
    module deliberately treats it as an injectable producer and owns the
    fail-closed replacement decision.
    """

    kind: PrimitiveKind | str
    path_data: str
    contour_error_px: float
    area_error_ratio: float
    topology: TopologySignature


@dataclass(frozen=True)
class FinalRenderEvidence:
    """Evidence that the proposed path passed a real original-size render gate."""

    source_width: int
    source_height: int
    rendered_width: int
    rendered_height: int
    passed: bool

    @property
    def is_original_resolution(self) -> bool:
        return (
            type(self.source_width) is int
            and type(self.source_height) is int
            and type(self.rendered_width) is int
            and type(self.rendered_height) is int
            and self.source_width > 0
            and self.source_height > 0
            and self.rendered_width == self.source_width
            and self.rendered_height == self.source_height
        )


@dataclass(frozen=True)
class PrimitiveFitResult:
    path_data: str
    replaced: bool
    primitive: PrimitiveKind | None
    gates: Mapping[str, bool]
    rejection_reasons: tuple[str, ...]


RenderGate = Callable[[str], FinalRenderEvidence]


def _safe_path_data(path_data: str, topology: TopologySignature) -> bool:
    if not isinstance(path_data, str):
        return False
    stripped = path_data.strip()
    if not stripped or not _SAFE_PATH_DATA.fullmatch(stripped) or not stripped.startswith("M"):
        return False
    subpaths = stripped.count("M")
    closures = stripped.count("Z")
    if subpaths != topology.subpaths:
        return False
    return closures == subpaths if topology.closed else closures == 0


def _compatible_topology(kind: PrimitiveKind, topology: TopologySignature) -> bool:
    if not topology.is_valid():
        return False
    if kind is PrimitiveKind.LINE:
        return not topology.closed and topology.subpaths == 1 and topology.holes == 0
    return topology.closed


def _finite_nonnegative(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0
    )


def apply_primitive_fit(
    *,
    original_path_data: str,
    original_topology: TopologySignature,
    proposal: PrimitiveProposal,
    render_gate: RenderGate | None,
    limits: PrimitiveFitLimits = PrimitiveFitLimits(),
) -> PrimitiveFitResult:
    """Return the proposed primitive only when every mandatory gate passes.

    Rendering is intentionally injected so the pipeline can use its verified
    SVG renderer. Missing or malformed evidence never authorizes replacement.
    """

    gates = {
        "supported_primitive": False,
        "safe_path_data": False,
        "contour_error": False,
        "area_error": False,
        "topology": False,
        "final_render": False,
    }
    reasons: list[str] = []

    try:
        kind = PrimitiveKind(proposal.kind)
    except (TypeError, ValueError):
        reasons.append("unsupported_primitive")
        return PrimitiveFitResult(original_path_data, False, None, gates, tuple(reasons))
    gates["supported_primitive"] = kind in SUPPORTED_PRIMITIVES

    gates["safe_path_data"] = isinstance(proposal.topology, TopologySignature) and _safe_path_data(
        proposal.path_data, proposal.topology
    )
    if not gates["safe_path_data"]:
        reasons.append("unsafe_path_data")

    contour_error = proposal.contour_error_px
    gates["contour_error"] = (
        limits.is_valid()
        and _finite_nonnegative(contour_error)
        and contour_error <= limits.maximum_contour_error_px
    )
    if not gates["contour_error"]:
        reasons.append("contour_error_gate")

    area_error = proposal.area_error_ratio
    gates["area_error"] = (
        limits.is_valid()
        and _finite_nonnegative(area_error)
        and area_error <= limits.maximum_area_error_ratio
    )
    if not gates["area_error"]:
        reasons.append("area_error_gate")

    gates["topology"] = (
        isinstance(original_topology, TopologySignature)
        and isinstance(proposal.topology, TopologySignature)
        and original_topology.is_valid()
        and proposal.topology == original_topology
        and _compatible_topology(kind, proposal.topology)
    )
    if not gates["topology"]:
        reasons.append("topology_gate")

    preliminary = all(gates[name] for name in gates if name != "final_render")
    if preliminary and render_gate is not None:
        try:
            render_evidence = render_gate(proposal.path_data)
        except Exception:
            reasons.append("final_render_error")
        else:
            gates["final_render"] = (
                isinstance(render_evidence, FinalRenderEvidence)
                and render_evidence.is_original_resolution
                and render_evidence.passed is True
            )
            if not gates["final_render"]:
                reasons.append("final_render_gate")
    elif preliminary:
        reasons.append("final_render_evidence_missing")

    if not all(gates.values()):
        return PrimitiveFitResult(original_path_data, False, kind, gates, tuple(reasons))
    return PrimitiveFitResult(proposal.path_data, True, kind, gates, ())
