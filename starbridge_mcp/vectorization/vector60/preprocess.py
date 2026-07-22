"""Non-destructive, scene-specific preprocessing for Vector60 candidates."""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from .scene_classifier import ScenePreset, validate_scene


@dataclass(frozen=True)
class PreprocessResult:
    """An in-memory image plus path-free processing metadata."""

    image: Image.Image
    scene: ScenePreset
    operations: tuple[str, ...]
    enhancement_allowed: bool

    def metadata(self) -> dict[str, object]:
        """Return report-safe metadata; image pixels are intentionally omitted."""

        return {
            "scene": self.scene,
            "operations": list(self.operations),
            "enhancement_allowed": self.enhancement_allowed,
            "width": self.image.width,
            "height": self.image.height,
        }


def _with_original_alpha(rgb: Image.Image, alpha: Image.Image) -> Image.Image:
    output = rgb.convert("RGBA")
    output.putalpha(alpha.copy())
    return output


def preprocess_image(image: Image.Image, scene: str) -> PreprocessResult:
    """Return a scene-tuned copy without writing files or changing ``image``.

    Photographic inputs are deliberately left unchanged. The pipeline must route
    that scene to its existing fallback instead of representing it as enhanced.
    """

    if not isinstance(image, Image.Image):
        raise TypeError("image must be a Pillow Image")
    if image.width < 1 or image.height < 1:
        raise ValueError("image dimensions must be positive")

    selected = validate_scene(scene)
    rgba = image.copy().convert("RGBA")
    alpha = rgba.getchannel("A")
    rgb = rgba.convert("RGB")

    if selected == "unsupported_photo":
        return PreprocessResult(
            image=rgba,
            scene=selected,
            operations=("identity_fallback",),
            enhancement_allowed=False,
        )

    if selected == "logo":
        processed = rgb.filter(ImageFilter.MedianFilter(size=3))
        processed = ImageEnhance.Contrast(processed).enhance(1.04)
        operations = ("median_denoise_3", "contrast_1.04")
    elif selected == "lineart":
        gray = ImageOps.autocontrast(ImageOps.grayscale(rgb), cutoff=0)
        gray = ImageEnhance.Contrast(gray).enhance(1.12)
        processed = Image.merge("RGB", (gray, gray, gray))
        operations = ("grayscale", "autocontrast", "contrast_1.12")
    elif selected == "flat":
        processed = rgb.filter(ImageFilter.MedianFilter(size=3))
        processed = ImageEnhance.Color(processed).enhance(1.03)
        operations = ("median_denoise_3", "color_1.03")
    else:
        processed = rgb.filter(ImageFilter.UnsharpMask(radius=0.8, percent=55, threshold=3))
        operations = ("unsharp_0.8_55_3",)

    return PreprocessResult(
        image=_with_original_alpha(processed, alpha),
        scene=selected,
        operations=operations,
        enhancement_allowed=True,
    )


def preprocess_for_scene(image: Image.Image, scene: str) -> PreprocessResult:
    """Readable alias for pipeline callers."""

    return preprocess_image(image, scene)


__all__ = ["PreprocessResult", "preprocess_for_scene", "preprocess_image"]
