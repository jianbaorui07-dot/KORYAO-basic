"""Generic WorldForge recipe, map, preview, and process validation."""

from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path
from typing import Any


PNG_HEADER = bytes([137, 80, 78, 71, 13, 10, 26, 10])


def load_recipe(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_recipe_schema(recipe: dict[str, Any]) -> dict[str, Any]:
    required = [
        "scene_id",
        "scene_name",
        "scene_revision",
        "framework_version",
        "mode",
        "map_asset_path",
        "style",
        "required_elements",
        "constraints",
        "preview_profile",
        "validation_profile",
    ]
    missing = [key for key in required if key not in recipe]
    return {"ok": not missing, "missing": missing}


def map_disk_path(project_root: Path, map_asset_path: str) -> Path:
    if not map_asset_path.startswith("/Game/"):
        raise ValueError(f"Unsupported map asset path: {map_asset_path}")
    return project_root / "Content" / Path((map_asset_path[6:] + ".umap").replace("/", "\\"))


def _png_chunks(data: bytes):
    offset = 8
    while offset + 8 <= len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        chunk = data[offset + 8 : offset + 8 + length]
        yield kind, chunk
        offset += 12 + length
        if kind == b"IEND":
            break


def _unfilter_scanlines(raw: bytes, width: int, height: int, channels: int) -> bytes:
    stride = width * channels
    result = bytearray()
    prior = bytearray(stride)
    pos = 0
    for _ in range(height):
        filter_type = raw[pos]
        pos += 1
        row = bytearray(raw[pos : pos + stride])
        pos += stride
        for i in range(stride):
            left = row[i - channels] if i >= channels else 0
            up = prior[i]
            up_left = prior[i - channels] if i >= channels else 0
            if filter_type == 1:
                row[i] = (row[i] + left) & 0xFF
            elif filter_type == 2:
                row[i] = (row[i] + up) & 0xFF
            elif filter_type == 3:
                row[i] = (row[i] + ((left + up) // 2)) & 0xFF
            elif filter_type == 4:
                p = left + up - up_left
                pa = abs(p - left)
                pb = abs(p - up)
                pc = abs(p - up_left)
                predictor = left if pa <= pb and pa <= pc else up if pb <= pc else up_left
                row[i] = (row[i] + predictor) & 0xFF
            elif filter_type != 0:
                raise ValueError(f"Unsupported PNG filter: {filter_type}")
        result.extend(row)
        prior = row
    return bytes(result)


def validate_png(path: str | Path, expected_width: int | None = None, expected_height: int | None = None) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        return {"ok": False, "exists": False, "error": "missing_png", "path": str(path)}
    data = path.read_bytes()
    if data[:8] != PNG_HEADER:
        return {"ok": False, "exists": True, "error": "invalid_png_header", "path": str(path), "size": len(data)}
    width = height = bit_depth = color_type = None
    idat = bytearray()
    for kind, chunk in _png_chunks(data):
        if kind == b"IHDR":
            width, height, bit_depth, color_type = struct.unpack(">IIBB", chunk[:10])
        elif kind == b"IDAT":
            idat.extend(chunk)
    issues: list[str] = []
    if len(data) <= 16 * 1024:
        issues.append("png_smaller_than_16kb")
    if expected_width and width != expected_width:
        issues.append("unexpected_width")
    if expected_height and height != expected_height:
        issues.append("unexpected_height")
    blank = None
    if bit_depth == 8 and color_type in (2, 6) and width and height and idat:
        channels = 3 if color_type == 2 else 4
        try:
            pixels = _unfilter_scanlines(zlib.decompress(bytes(idat)), width, height, channels)
            sample = pixels[:: max(1, len(pixels) // 4096)]
            blank = len(set(sample)) <= 2
            if blank:
                issues.append("png_appears_blank")
        except Exception as exc:
            issues.append(f"png_blank_check_failed:{exc}")
    return {
        "ok": not issues,
        "exists": True,
        "path": str(path),
        "size": len(data),
        "width": width,
        "height": height,
        "bit_depth": bit_depth,
        "color_type": color_type,
        "blank": blank,
        "issues": issues,
    }


def validate_scene_in_editor(recipe: dict[str, Any], project_root: Path) -> dict[str, Any]:
    import unreal  # type: ignore

    profile = recipe.get("validation_profile", {})
    map_path = recipe["map_asset_path"]
    disk_path = map_disk_path(project_root, map_path)
    checks: dict[str, Any] = {
        "map_asset_exists": unreal.EditorAssetLibrary.does_asset_exist(map_path),
        "map_file_exists": disk_path.exists(),
    }
    if checks["map_asset_exists"]:
        unreal.EditorLevelLibrary.load_level(map_path)
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    labels = [actor.get_actor_label() for actor in actors]
    checks["actor_count"] = len(actors)
    actor_min = profile.get("actor_count_min")
    actor_max = profile.get("actor_count_max")
    checks["actor_count_in_range"] = (
        (actor_min is None or len(actors) >= actor_min) and (actor_max is None or len(actors) <= actor_max)
    )
    required_labels = profile.get("required_labels", [])
    checks["required_labels_present"] = all(label in labels for label in required_labels)
    required_tags = profile.get("required_tags", [])
    if required_tags:
        tagged = [
            actor
            for actor in actors
            if all(tag in [str(item) for item in actor.tags] for tag in required_tags)
        ]
        checks["required_tags_present"] = bool(tagged)
    checks["camera_readable"] = any("Camera" in actor.get_class().get_name() or "Camera" in actor.get_actor_label() for actor in actors)
    ok = all(value for key, value in checks.items() if key != "actor_count")
    return {"ok": ok, "checks": checks, "labels": labels}
