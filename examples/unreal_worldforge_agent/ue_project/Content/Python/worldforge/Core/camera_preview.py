"""Generic camera preview capture for a WorldForge recipe.

Run inside visible UnrealEditor with:
  -ExecCmds="py exec(open(r'.../camera_preview.py').read())"
"""

from __future__ import annotations

import json
import math
import os
import shutil
import sys
import time
import traceback
import struct
import zlib
from datetime import datetime
from pathlib import Path
from typing import Any


def _bootstrap() -> Path:
    script_path = Path(__file__).resolve()
    python_root = script_path.parents[2]
    if str(python_root) not in sys.path:
        sys.path.insert(0, str(python_root))
    return script_path.parents[4]


PROJECT_ROOT = Path(os.environ.get("WORLDFORGE_PROJECT_ROOT") or _bootstrap()).resolve()
from worldforge.Core import recipe_path_resolver, scene_validator, state_manager  # noqa: E402

import unreal  # type: ignore  # noqa: E402


RECIPE_PATH = recipe_path_resolver.resolve(os.environ["WORLDFORGE_RECIPE_PATH"], PROJECT_ROOT)
RECIPE = scene_validator.load_recipe(RECIPE_PATH)
SCENE_ID = RECIPE["scene_id"]
SCENE_REVISION = RECIPE.get("scene_revision", "R1")
MAP_PATH = RECIPE["map_asset_path"]
PROFILE = RECIPE.get("preview_profile", {})
WIDTH = int(PROFILE.get("width", 1280))
HEIGHT = int(PROFILE.get("height", 720))
PREVIEW_PATH = Path(os.environ.get("WORLDFORGE_PREVIEW_PATH") or PROFILE.get("target_path") or rf"<WORLDFORGE_RUNTIME>\Previews\{SCENE_ID}_{SCENE_REVISION}_preview.png")
RECEIPT_PATH = Path(os.environ.get("WORLDFORGE_PREVIEW_RECEIPT") or rf"<WORLDFORGE_RUNTIME>\Logs\{SCENE_ID}_{SCENE_REVISION}_preview_receipt.json")
SCREENSHOT_NAME = PREVIEW_PATH.stem
TIMEOUT_SECONDS = float(PROFILE.get("timeout_seconds", 90))

_tick_handle: Any | None = None
_task: Any | None = None
_started = time.monotonic()
_started_wall = time.time()
_last_check = 0.0
_stable_signature: tuple[int, float] | None = None
_stable_seen = 0.0
_finished = False
_receipt: dict[str, Any] = {
    "job_id": f"{SCENE_ID}_{SCENE_REVISION}_preview",
    "scene_id": SCENE_ID,
    "recipe_path": str(RECIPE_PATH),
    "map_asset_path": MAP_PATH,
    "preview_path": str(PREVIEW_PATH),
    "width": WIDTH,
    "height": HEIGHT,
    "status": "starting",
    "started_at": datetime.now().astimezone().isoformat(),
    "checks": [],
}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


PNG_HEADER = bytes([137, 80, 78, 71, 13, 10, 26, 10])


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


def validate_png_file(path: Path, expected_width: int, expected_height: int) -> dict[str, Any]:
    if not path.exists():
        return {"ok": False, "exists": False, "path": str(path), "error": "missing_png"}
    data = path.read_bytes()
    status: dict[str, Any] = {
        "ok": False,
        "exists": True,
        "path": str(path),
        "file_size": len(data),
        "png_header_valid": data[:8] == PNG_HEADER,
        "width": None,
        "height": None,
        "issues": [],
    }
    if not status["png_header_valid"]:
        status["issues"].append("invalid_png_header")
        return status
    bit_depth = color_type = None
    for kind, chunk in _png_chunks(data):
        if kind == b"IHDR":
            width, height, bit_depth, color_type = struct.unpack(">IIBB", chunk[:10])
            status.update({"width": width, "height": height, "bit_depth": bit_depth, "color_type": color_type})
            break
    if status["file_size"] <= int(PROFILE.get("min_bytes", 16384)):
        status["issues"].append("png_smaller_than_min_bytes")
    if status["width"] != expected_width:
        status["issues"].append("unexpected_width")
    if status["height"] != expected_height:
        status["issues"].append("unexpected_height")
    status["ok"] = not status["issues"]
    return status


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


def _luminance_grid(path: Path) -> tuple[dict[str, Any], list[list[float]]]:
    data = path.read_bytes()
    width = height = bit_depth = color_type = interlace = None
    idat = bytearray()
    for kind, chunk in _png_chunks(data):
        if kind == b"IHDR":
            width, height, bit_depth, color_type = struct.unpack(">IIBB", chunk[:10])
            interlace = chunk[12]
        elif kind == b"IDAT":
            idat.extend(chunk)
    meta = {
        "width": width,
        "height": height,
        "bit_depth": bit_depth,
        "color_type": color_type,
        "interlace": interlace,
    }
    if not width or not height or bit_depth != 8 or color_type not in (2, 6) or interlace not in (0, None):
        return meta, []
    channels = 3 if color_type == 2 else 4
    pixels = _unfilter_scanlines(zlib.decompress(bytes(idat)), width, height, channels)
    step_x = max(1, width // 160)
    step_y = max(1, height // 90)
    grid: list[list[float]] = []
    for y in range(0, height, step_y):
        row: list[float] = []
        for x in range(0, width, step_x):
            pos = (y * width + x) * channels
            r, g, b = pixels[pos], pixels[pos + 1], pixels[pos + 2]
            row.append((0.2126 * r) + (0.7152 * g) + (0.0722 * b))
        grid.append(row)
    return meta, grid


def _stddev(values: list[float]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / len(values))


def preview_visual_metrics(path: Path, expected_width: int, expected_height: int) -> dict[str, Any]:
    file_status = validate_png_file(path, expected_width, expected_height)
    metrics: dict[str, Any] = {
        "width": file_status.get("width"),
        "height": file_status.get("height"),
        "file_size": file_status.get("file_size"),
        "png_header_valid": file_status.get("png_header_valid", False),
        "luminance_min": None,
        "luminance_max": None,
        "luminance_stddev": None,
        "edge_density": None,
        "non_uniform_regions": None,
        "visual_status": "INCONCLUSIVE",
        "reason": "visual_metrics_not_available",
    }
    if not file_status.get("ok"):
        metrics["visual_status"] = "FAIL"
        metrics["reason"] = "png_file_status_failed:" + ",".join(file_status.get("issues", [file_status.get("error", "unknown")]))
        return metrics
    try:
        _, grid = _luminance_grid(path)
    except Exception as exc:
        metrics["reason"] = f"visual_metric_decode_failed:{exc}"
        return metrics
    values = [value for row in grid for value in row]
    if not values:
        return metrics
    lum_min = min(values)
    lum_max = max(values)
    lum_std = _stddev(values)
    edge_hits = 0
    edge_total = 0
    for row in grid:
        for left, right in zip(row, row[1:]):
            edge_hits += 1 if abs(left - right) >= 20 else 0
            edge_total += 1
    for upper, lower in zip(grid, grid[1:]):
        for a, b in zip(upper, lower):
            edge_hits += 1 if abs(a - b) >= 20 else 0
            edge_total += 1
    edge_density = edge_hits / edge_total if edge_total else 0.0
    non_uniform_regions = 0
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    for ry in range(6):
        y0 = rows * ry // 6
        y1 = rows * (ry + 1) // 6
        for rx in range(8):
            x0 = cols * rx // 8
            x1 = cols * (rx + 1) // 8
            region = [grid[y][x] for y in range(y0, y1) for x in range(x0, x1)]
            if region and _stddev(region) >= 4.0 and (max(region) - min(region)) >= 8.0:
                non_uniform_regions += 1
    metrics.update(
        {
            "luminance_min": round(lum_min, 3),
            "luminance_max": round(lum_max, 3),
            "luminance_stddev": round(lum_std, 3),
            "edge_density": round(edge_density, 6),
            "non_uniform_regions": non_uniform_regions,
        }
    )
    if lum_max <= 3 and lum_std < 1 and edge_density < 0.001:
        metrics["visual_status"] = "FAIL"
        metrics["reason"] = "near_black_uniform_frame"
    elif lum_std < 1 and edge_density < 0.001 and non_uniform_regions == 0:
        metrics["visual_status"] = "FAIL"
        metrics["reason"] = "uniform_frame_no_visible_detail"
    elif (edge_density >= 0.01 and non_uniform_regions >= 4 and (lum_max - lum_min) >= 12) or (
        lum_std >= 8 and non_uniform_regions >= 6
    ):
        metrics["visual_status"] = "PASS"
        metrics["reason"] = "visible_detail_edges_and_regions_detected"
    else:
        metrics["visual_status"] = "INCONCLUSIVE"
        metrics["reason"] = "file_valid_but_visual_detail_below_confident_pass_threshold"
    return metrics


def _vector_dict(value: Any) -> dict[str, float]:
    return {"x": round(float(value.x), 3), "y": round(float(value.y), 3), "z": round(float(value.z), 3)}


def _rotator_dict(value: Any) -> dict[str, float]:
    return {
        "pitch": round(float(value.pitch), 3),
        "yaw": round(float(value.yaw), 3),
        "roll": round(float(value.roll), 3),
    }


def camera_metadata(camera: Any) -> dict[str, Any]:
    component = None
    for attr in ("get_cine_camera_component", "cine_camera_component", "camera_component"):
        value = getattr(camera, attr, None)
        try:
            component = value() if callable(value) else value
        except Exception:
            component = None
        if component is not None:
            break
    fov = None
    near_clip = None
    if component is not None:
        for prop in ("field_of_view", "current_focal_length"):
            try:
                value = component.get_editor_property(prop)
                if value is not None:
                    fov = float(value)
                    break
            except Exception:
                pass
        for prop in ("custom_near_clipping_plane", "near_clip_plane"):
            try:
                value = component.get_editor_property(prop)
                if value is not None:
                    near_clip = float(value)
                    break
            except Exception:
                pass
    return {
        "label": camera.get_actor_label(),
        "class": camera.get_class().get_name(),
        "location": _vector_dict(camera.get_actor_location()),
        "rotation": _rotator_dict(camera.get_actor_rotation()),
        "fov_or_focal_length": fov,
        "near_clip": near_clip,
    }


def map_status() -> dict[str, Any]:
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    labels = [actor.get_actor_label() for actor in actors]
    classes = {actor.get_actor_label(): actor.get_class().get_name() for actor in actors}
    required = RECIPE.get("validation_profile", {}).get("required_labels", [])
    return {
        "asset_exists": unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH),
        "actor_count": len(actors),
        "required_labels_present": all(label in labels for label in required),
        "directional_light_loaded": any("DirectionalLight" in cls for cls in classes.values()),
        "sky_light_loaded": any("SkyLight" in cls for cls in classes.values()),
        "fog_loaded": any("ExponentialHeightFog" in cls for cls in classes.values()),
    }


def find_camera():
    preferred = PROFILE.get("camera_label_contains")
    fallback = None
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        label = actor.get_actor_label()
        cls = actor.get_class().get_name()
        if preferred and preferred in label:
            return actor
        if fallback is None and ("CineCameraActor" in cls or "Camera" in cls or "Camera" in label):
            fallback = actor
    return fallback


def frame_camera(camera) -> None:
    try:
        unreal.EditorLevelLibrary.set_level_viewport_camera_info(camera.get_actor_location(), camera.get_actor_rotation())
    except Exception as exc:
        _receipt["viewport_warning"] = str(exc)


def task_done(task: Any) -> bool:
    for name in ("is_task_done", "is_done", "is_complete", "is_task_complete"):
        method = getattr(task, name, None)
        if callable(method):
            try:
                return bool(method())
            except Exception:
                pass
    return bool(task)


def png_valid(path: Path) -> bool:
    result = validate_png_file(path, WIDTH, HEIGHT)
    return bool(result.get("ok"))


def copy_recent_png() -> str | None:
    if PREVIEW_PATH.exists():
        return None
    search_roots = [
        PROJECT_ROOT / "Saved" / "Screenshots",
        PROJECT_ROOT / "Saved" / "Screenshots" / "Windows",
        PROJECT_ROOT / "Saved" / "Screenshots" / "WindowsEditor",
    ]
    try:
        search_roots.append(Path(unreal.Paths.screen_shot_dir()))
    except Exception:
        pass
    candidates: list[Path] = []
    for root in search_roots:
        if not root.exists():
            continue
        for path in root.rglob("*.png"):
            try:
                if path.stat().st_mtime >= _started_wall - 2 and path.stem == SCREENSHOT_NAME and png_valid(path):
                    candidates.append(path)
            except OSError:
                continue
    if not candidates:
        return None
    source = max(candidates, key=lambda item: item.stat().st_mtime)
    PREVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, PREVIEW_PATH)
    return str(source)


def finish(status: str, phase: str, error: str | None = None) -> None:
    global _finished
    _finished = True
    _receipt["status"] = status
    _receipt["finished_at"] = datetime.now().astimezone().isoformat()
    _receipt["elapsed_seconds"] = round(time.monotonic() - _started, 2)
    file_status = validate_png_file(PREVIEW_PATH, WIDTH, HEIGHT)
    visual_metrics = preview_visual_metrics(PREVIEW_PATH, WIDTH, HEIGHT)
    _receipt["preview_file_status"] = file_status
    _receipt["preview_visual_status"] = visual_metrics.get("visual_status")
    _receipt["visual_metrics"] = visual_metrics
    _receipt["preview_validation"] = file_status
    if error:
        _receipt["error"] = error
    write_json(RECEIPT_PATH, _receipt)
    state_manager.write_state(
        {
            "phase": phase,
            "framework_version": state_manager.FRAMEWORK_VERSION,
            "active_scene_id": SCENE_ID,
            "active_recipe_path": str(RECIPE_PATH),
            "requested_map_path": MAP_PATH,
            "job_phase": phase,
            "map_status": _receipt.get("map_status"),
            "preview_exists": bool(file_status.get("ok")),
            "preview_file_status": file_status,
            "preview_visual_status": visual_metrics.get("visual_status"),
            "preview_path": str(PREVIEW_PATH),
            "editor_status": "PREVIEW_EDITOR_QUIT_REQUESTED" if os.environ.get("WORLDFORGE_QUIT_AFTER_PREVIEW") == "1" else "PREVIEW_SESSION_ACTIVE",
            "last_error": error or "",
        },
        PROJECT_ROOT,
    )
    try:
        if _tick_handle is not None:
            unreal.unregister_slate_post_tick_callback(_tick_handle)
    except Exception as exc:
        unreal.log_warning(f"[WorldForge] Could not unregister preview tick: {exc}")
    if os.environ.get("WORLDFORGE_QUIT_AFTER_PREVIEW") == "1":
        unreal.SystemLibrary.quit_editor()


def on_tick(delta_seconds: float) -> None:
    global _last_check, _stable_signature, _stable_seen
    if _finished:
        return
    now = time.monotonic()
    if now - _last_check < 1.0:
        return
    _last_check = now
    copied_from = copy_recent_png()
    validation = validate_png_file(PREVIEW_PATH, WIDTH, HEIGHT)
    _receipt["checks"].append(
        {
            "elapsed_seconds": round(now - _started, 2),
            "task_done": task_done(_task),
            "target_png_exists": validation.get("exists", False),
            "target_png_valid": validation.get("ok", False),
            "target_png_size": validation.get("file_size"),
            "copied_from": copied_from,
        }
    )
    if validation.get("ok"):
        stat = PREVIEW_PATH.stat()
        signature = (stat.st_size, stat.st_mtime)
        if _stable_signature == signature and now - _stable_seen >= 1.0:
            finish("preview_ready", "PREVIEW_READY")
            return
        _stable_signature = signature
        _stable_seen = now
    if now - _started >= TIMEOUT_SECONDS:
        finish("preview_timeout", "PREVIEW_TIMEOUT", "preview_png_not_ready_within_timeout")


def start() -> None:
    global _tick_handle, _task
    try:
        state_manager.write_state(
            {
                "phase": "PREVIEW_RUNNING",
                "job_phase": "PREVIEW_RUNNING",
                "active_scene_id": SCENE_ID,
                "editor_status": "PREVIEW_EDITOR_RUNNING",
            },
            PROJECT_ROOT,
        )
        if not unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
            raise RuntimeError(f"Map asset missing: {MAP_PATH}")
        unreal.EditorLevelLibrary.load_level(MAP_PATH)
        _receipt["map_status"] = map_status()
        camera = find_camera()
        if camera is None:
            raise RuntimeError("No readable camera actor found")
        _receipt["camera_label"] = camera.get_actor_label()
        _receipt["camera_class"] = camera.get_class().get_name()
        _receipt["camera_transform"] = camera_metadata(camera)
        _receipt["camera_fov"] = _receipt["camera_transform"].get("fov_or_focal_length")
        frame_camera(camera)
        if PREVIEW_PATH.exists():
            PREVIEW_PATH.unlink()
        _task = unreal.AutomationLibrary.take_high_res_screenshot(WIDTH, HEIGHT, SCREENSHOT_NAME, camera)
        _receipt["automation_screenshot_name"] = SCREENSHOT_NAME
        _receipt["automation_task_type"] = type(_task).__name__
        _receipt["status"] = "screenshot_requested"
        write_json(RECEIPT_PATH, _receipt)
        _tick_handle = unreal.register_slate_post_tick_callback(on_tick)
    except Exception as exc:
        _receipt["traceback"] = traceback.format_exc()
        write_json(RECEIPT_PATH, _receipt)
        finish("failed", "FAILED", str(exc))
        raise


start()
