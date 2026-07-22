"""Deterministic, local-only scene heuristics for Vector60.

The classifier deliberately returns compact statistical reason codes. It does
not retain source paths, image bytes, colour samples, or other material content.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal, cast

import numpy as np
from PIL import Image, ImageFilter

ScenePreset = Literal["logo", "lineart", "flat", "illustration", "unsupported_photo"]

SUPPORTED_SCENES: tuple[ScenePreset, ...] = (
    "logo",
    "lineart",
    "flat",
    "illustration",
    "unsupported_photo",
)


@dataclass(frozen=True)
class SceneFeatures:
    """Path-free aggregate measurements used by the heuristic classifier."""

    quantized_color_count: int
    color_entropy: float
    dominant_color_ratio: float
    low_saturation_ratio: float
    mean_saturation: float
    edge_density: float
    high_frequency_ratio: float
    luminance_range: float
    transparent_ratio: float

    def as_dict(self) -> dict[str, int | float]:
        """Return stable, JSON-friendly aggregate values."""

        return asdict(self)


@dataclass(frozen=True)
class SceneClassification:
    """A deterministic scene decision with non-sensitive explanation codes."""

    scene: ScenePreset
    confidence: float
    reasons: tuple[str, ...]
    features: SceneFeatures

    def as_dict(self) -> dict[str, object]:
        """Return report-safe classification metadata."""

        return {
            "scene": self.scene,
            "confidence": self.confidence,
            "reasons": list(self.reasons),
            "features": self.features.as_dict(),
        }


def _analysis_image(image: Image.Image, maximum_side: int = 256) -> Image.Image:
    if not isinstance(image, Image.Image):
        raise TypeError("image must be a Pillow Image")
    if image.width < 1 or image.height < 1:
        raise ValueError("image dimensions must be positive")
    sample = image.copy().convert("RGBA")
    scale = min(1.0, maximum_side / max(sample.size))
    if scale < 1.0:
        size = (
            max(1, round(sample.width * scale)),
            max(1, round(sample.height * scale)),
        )
        sample = sample.resize(size, Image.Resampling.LANCZOS)
    return sample


def _entropy(counts: np.ndarray) -> float:
    probabilities = counts[counts > 0].astype(np.float64)
    probabilities /= probabilities.sum()
    return float(-(probabilities * np.log2(probabilities)).sum())


def extract_scene_features(image: Image.Image) -> SceneFeatures:
    """Measure only aggregate visual statistics from an in-memory image."""

    sample = _analysis_image(image)
    rgba = np.asarray(sample, dtype=np.uint8)
    alpha = rgba[..., 3].astype(np.float32) / 255.0
    rgb = rgba[..., :3].astype(np.float32) / 255.0

    # Transparent pixels are composited for analysis only. The caller's image is
    # never changed, and alpha remains available as a useful logo signal.
    composed = rgb * alpha[..., None] + (1.0 - alpha[..., None])
    maximum = composed.max(axis=2)
    minimum = composed.min(axis=2)
    saturation = np.divide(
        maximum - minimum,
        maximum,
        out=np.zeros_like(maximum),
        where=maximum > 1e-6,
    )
    luminance = composed[..., 0] * 0.2126 + composed[..., 1] * 0.7152 + composed[..., 2] * 0.0722

    quantized = np.minimum((composed * 15.999).astype(np.uint8), 15)
    packed = (
        quantized[..., 0].astype(np.int32) * 256
        + quantized[..., 1].astype(np.int32) * 16
        + quantized[..., 2].astype(np.int32)
    )
    counts = np.bincount(packed.ravel(), minlength=4096)
    occupied = counts[counts > 0]

    horizontal = np.abs(np.diff(luminance, axis=1))
    vertical = np.abs(np.diff(luminance, axis=0))
    edge_values = np.concatenate((horizontal.ravel(), vertical.ravel()))
    edge_density = float(np.mean(edge_values >= 0.12)) if edge_values.size else 0.0

    blurred = (
        np.asarray(
            Image.fromarray(np.round(luminance * 255).astype(np.uint8)).filter(
                ImageFilter.GaussianBlur(radius=1.0)
            ),
            dtype=np.float32,
        )
        / 255.0
    )
    residual = np.abs(luminance - blurred)

    return SceneFeatures(
        quantized_color_count=int(occupied.size),
        color_entropy=round(_entropy(occupied), 6),
        dominant_color_ratio=round(float(occupied.max() / packed.size), 6),
        low_saturation_ratio=round(float(np.mean(saturation <= 0.10)), 6),
        mean_saturation=round(float(np.mean(saturation)), 6),
        edge_density=round(edge_density, 6),
        high_frequency_ratio=round(float(np.mean(residual >= 0.035)), 6),
        luminance_range=round(float(np.percentile(luminance, 95) - np.percentile(luminance, 5)), 6),
        transparent_ratio=round(float(np.mean(alpha < 0.98)), 6),
    )


def _result(
    scene: ScenePreset,
    confidence: float,
    reasons: tuple[str, ...],
    features: SceneFeatures,
) -> SceneClassification:
    return SceneClassification(
        scene=scene,
        confidence=round(max(0.5, min(0.99, confidence)), 3),
        reasons=reasons,
        features=features,
    )


def classify_scene(image: Image.Image) -> SceneClassification:
    """Classify a scene conservatively using deterministic local heuristics.

    ``unsupported_photo`` requires several independent photographic signals.
    Ambiguous or generated artwork remains ``illustration`` so the caller can
    still evaluate it through the normal Vector60 quality gates.
    """

    features = extract_scene_features(image)

    photo_signals = (
        features.quantized_color_count >= 220,
        features.color_entropy >= 6.25,
        features.high_frequency_ratio >= 0.22,
        features.edge_density >= 0.10,
        features.dominant_color_ratio <= 0.10,
        features.luminance_range >= 0.58,
    )
    photo_score = sum(photo_signals)
    if photo_score >= 5:
        return _result(
            "unsupported_photo",
            0.70 + 0.045 * photo_score,
            ("high_color_complexity", "continuous_texture", "photo_gate_passed"),
            features,
        )

    lineart_signals = (
        features.low_saturation_ratio >= 0.90,
        0.008 <= features.edge_density <= 0.22,
        features.luminance_range >= 0.45,
        features.dominant_color_ratio >= 0.48,
    )
    if sum(lineart_signals) >= 3 and features.transparent_ratio <= 0.02:
        return _result(
            "lineart",
            0.66 + 0.065 * sum(lineart_signals),
            ("mostly_achromatic", "sparse_contrast_edges"),
            features,
        )

    logo_signals = (
        features.quantized_color_count <= 24,
        features.color_entropy <= 3.25,
        features.dominant_color_ratio >= 0.36,
        features.edge_density <= 0.16,
        features.transparent_ratio >= 0.05,
    )
    if sum(logo_signals) >= 4:
        return _result(
            "logo",
            0.64 + 0.06 * sum(logo_signals),
            ("compact_palette", "large_uniform_regions"),
            features,
        )

    flat_signals = (
        features.quantized_color_count <= 64,
        features.color_entropy <= 4.50,
        features.dominant_color_ratio >= 0.18,
        features.high_frequency_ratio <= 0.16,
    )
    if sum(flat_signals) >= 3:
        return _result(
            "flat",
            0.60 + 0.07 * sum(flat_signals),
            ("limited_palette", "broad_flat_regions"),
            features,
        )

    illustration_reasons = ["mixed_shape_and_color_detail"]
    if photo_score:
        illustration_reasons.append("photo_evidence_below_gate")
    return _result(
        "illustration",
        0.58 + 0.025 * max(0, 4 - photo_score),
        tuple(illustration_reasons),
        features,
    )


def validate_scene(scene: str) -> ScenePreset:
    """Validate a serialized scene name without accepting undocumented modes."""

    if scene not in SUPPORTED_SCENES:
        raise ValueError("scene must be one of the supported Vector60 presets")
    return cast(ScenePreset, scene)


__all__ = [
    "SUPPORTED_SCENES",
    "SceneClassification",
    "SceneFeatures",
    "ScenePreset",
    "classify_scene",
    "extract_scene_features",
    "validate_scene",
]
