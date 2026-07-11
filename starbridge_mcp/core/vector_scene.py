from __future__ import annotations

import math
import re
from html import escape
from typing import Any

from starbridge_mcp.core.security import sanitize

ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$")
COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$")
OBJECT_TYPES = {"rect", "circle", "ellipse", "line", "polygon", "path", "text"}
COMMON_OBJECT_FIELDS = {"id", "layer_id", "name", "type", "style"}
TYPE_FIELDS = {
    "rect": {"x", "y", "width", "height", "rx"},
    "circle": {"cx", "cy", "r"},
    "ellipse": {"cx", "cy", "rx_radius", "ry_radius"},
    "line": {"x1", "y1", "x2", "y2"},
    "polygon": {"points"},
    "path": {"commands"},
    "text": {"x", "y", "text", "font_family", "font_size", "text_anchor"},
}
REQUIRED_TYPE_FIELDS = {
    "rect": {"x", "y", "width", "height"},
    "circle": {"cx", "cy", "r"},
    "ellipse": {"cx", "cy", "rx_radius", "ry_radius"},
    "line": {"x1", "y1", "x2", "y2"},
    "polygon": {"points"},
    "path": {"commands"},
    "text": {"x", "y", "text", "font_family", "font_size"},
}


def _number(value: Any, *, name: str, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be a finite number")
    if not -100000 <= number <= 100000:
        raise ValueError(f"{name} is outside supported coordinate range")
    if positive and number <= 0:
        raise ValueError(f"{name} must be positive")
    return number


def _format_number(value: Any) -> str:
    number = _number(value, name="SVG number")
    if number == 0:
        return "0"
    return f"{number:.4f}".rstrip("0").rstrip(".")


def _validate_id(value: Any, *, name: str) -> None:
    if not isinstance(value, str) or not ID_PATTERN.fullmatch(value):
        raise ValueError(f"{name} must be a safe identifier")


def _resolve_paint(value: Any, palette: dict[str, str], *, name: str) -> str:
    if value is None:
        return "none"
    if not isinstance(value, str):
        raise TypeError(f"{name} must be color, palette token, or null")
    if value.startswith("@"):
        token = value[1:]
        if token not in palette:
            raise ValueError(f"unknown palette token: {token}")
        return palette[token]
    if not COLOR_PATTERN.fullmatch(value):
        raise ValueError(f"{name} must be a hex color or palette token")
    return value.upper()


def validate_vector_scene(scene: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    try:
        if scene.get("schema_version") != "starbridge.vector-scene.v1":
            failures.append("unsupported schema_version")
        _validate_id(scene.get("scene_id"), name="scene_id")
        document = scene["document"]
        _number(document["width"], name="document.width", positive=True)
        _number(document["height"], name="document.height", positive=True)
        if document.get("units") not in {"px", "pt", "mm"}:
            failures.append("unsupported document units")
        if document.get("color_mode") not in {"RGB", "CMYK"}:
            failures.append("unsupported color mode")
        background = document.get("background")
        if background is not None and not COLOR_PATTERN.fullmatch(str(background)):
            failures.append("document.background must be hex color or null")

        palette = scene.get("palette", {})
        if not isinstance(palette, dict) or len(palette) > 64:
            failures.append("palette must be an object with at most 64 colors")
            palette = {}
        for token, color in palette.items():
            if not re.fullmatch(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$", str(token)):
                failures.append(f"invalid palette token: {token}")
            if not COLOR_PATTERN.fullmatch(str(color)):
                failures.append(f"invalid palette color: {token}")

        layers = scene["layers"]
        if not isinstance(layers, list) or not layers or len(layers) > 128:
            failures.append("layers must contain 1..128 items")
            layers = []
        layer_ids: list[str] = []
        for layer in layers:
            _validate_id(layer.get("id"), name="layer.id")
            layer_ids.append(layer["id"])
            if not isinstance(layer.get("name"), str) or not layer["name"]:
                failures.append(f"layer name is required: {layer.get('id')}")
            if not isinstance(layer.get("visible"), bool) or not isinstance(
                layer.get("locked"), bool
            ):
                failures.append(f"layer visibility and lock flags must be bool: {layer.get('id')}")
        if len(layer_ids) != len(set(layer_ids)):
            failures.append("layer ids must be unique")

        objects = scene["objects"]
        if not isinstance(objects, list) or len(objects) > 10000:
            failures.append("objects must be a list with at most 10000 items")
            objects = []
        object_ids: list[str] = []
        for item in objects:
            _validate_object(item, set(layer_ids), palette)
            object_ids.append(item["id"])
        if len(object_ids) != len(set(object_ids)):
            failures.append("object ids must be unique")
    except (KeyError, TypeError, ValueError) as exc:
        failures.append(str(exc))
    return failures


def _validate_object(item: dict[str, Any], layer_ids: set[str], palette: dict[str, str]) -> None:
    if not isinstance(item, dict):
        raise TypeError("vector object must be dict")
    _validate_id(item.get("id"), name="object.id")
    _validate_id(item.get("layer_id"), name="object.layer_id")
    if item["layer_id"] not in layer_ids:
        raise ValueError(f"unknown layer_id for object {item['id']}")
    object_type = item.get("type")
    if object_type not in OBJECT_TYPES:
        raise ValueError(f"unsupported vector object type: {object_type}")
    allowed = COMMON_OBJECT_FIELDS | TYPE_FIELDS[object_type]
    extra = sorted(set(item) - allowed)
    if extra:
        raise ValueError(f"unsupported fields for {object_type}: {', '.join(extra)}")
    missing = sorted(REQUIRED_TYPE_FIELDS[object_type] - set(item))
    if missing:
        raise ValueError(f"missing fields for {object_type}: {', '.join(missing)}")
    style = item.get("style")
    if not isinstance(style, dict):
        raise TypeError("object.style must be dict")
    required_style = {"fill", "stroke", "stroke_width", "opacity"}
    if not required_style.issubset(style):
        raise ValueError("object.style is missing required fields")
    if set(style) - required_style - {"line_cap", "line_join"}:
        raise ValueError("object.style contains unsupported fields")
    _resolve_paint(style["fill"], palette, name="fill")
    _resolve_paint(style["stroke"], palette, name="stroke")
    stroke_width = _number(style["stroke_width"], name="stroke_width")
    opacity = _number(style["opacity"], name="opacity")
    if stroke_width < 0 or not 0 <= opacity <= 1:
        raise ValueError("stroke_width or opacity is outside supported range")

    if object_type == "rect":
        for key in ("x", "y"):
            _number(item[key], name=key)
        for key in ("width", "height"):
            _number(item[key], name=key, positive=True)
        if "rx" in item and _number(item["rx"], name="rx") < 0:
            raise ValueError("rx must not be negative")
    elif object_type == "circle":
        _number(item["cx"], name="cx")
        _number(item["cy"], name="cy")
        _number(item["r"], name="r", positive=True)
    elif object_type == "ellipse":
        _number(item["cx"], name="cx")
        _number(item["cy"], name="cy")
        _number(item["rx_radius"], name="rx_radius", positive=True)
        _number(item["ry_radius"], name="ry_radius", positive=True)
    elif object_type == "line":
        for key in ("x1", "y1", "x2", "y2"):
            _number(item[key], name=key)
    elif object_type == "polygon":
        points = item["points"]
        if not isinstance(points, list) or not 2 <= len(points) <= 4096:
            raise ValueError("polygon.points must contain 2..4096 points")
        for point in points:
            if not isinstance(point, list) or len(point) != 2:
                raise ValueError("polygon point must contain x and y")
            _number(point[0], name="point.x")
            _number(point[1], name="point.y")
    elif object_type == "path":
        _validate_commands(item["commands"])
    elif object_type == "text":
        _number(item["x"], name="text.x")
        _number(item["y"], name="text.y")
        _number(item["font_size"], name="font_size", positive=True)
        if not isinstance(item["text"], str) or len(item["text"]) > 4096:
            raise ValueError("text must be a string with at most 4096 characters")
        if not isinstance(item["font_family"], str) or not item["font_family"]:
            raise ValueError("font_family must not be empty")
        if item.get("text_anchor", "start") not in {"start", "middle", "end"}:
            raise ValueError("unsupported text_anchor")


def _validate_commands(commands: Any) -> None:
    if not isinstance(commands, list) or not 1 <= len(commands) <= 4096:
        raise ValueError("path.commands must contain 1..4096 commands")
    if not isinstance(commands[0], dict) or commands[0].get("op") != "M":
        raise ValueError("path must start with M")
    for command in commands:
        if not isinstance(command, dict):
            raise TypeError("path command must be dict")
        op = command.get("op")
        required = {"M": {"op", "x", "y"}, "L": {"op", "x", "y"}, "C": {"op", "x1", "y1", "x2", "y2", "x", "y"}, "Z": {"op"}}
        if op not in required or set(command) != required[op]:
            raise ValueError(f"invalid path command: {op}")
        for key, value in command.items():
            if key != "op":
                _number(value, name=f"path.{key}")


def compile_vector_scene_to_svg(scene: dict[str, Any]) -> str:
    failures = validate_vector_scene(scene)
    if failures:
        raise ValueError("invalid vector scene: " + "; ".join(failures))
    document = scene["document"]
    width = _format_number(document["width"])
    height = _format_number(document["height"])
    palette = {name: color.upper() for name, color in scene["palette"].items()}
    objects_by_layer: dict[str, list[dict[str, Any]]] = {
        layer["id"]: [] for layer in scene["layers"]
    }
    for item in scene["objects"]:
        objects_by_layer[item["layer_id"]].append(item)

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" data-color-mode="{document["color_mode"]}">'
        ),
    ]
    if document["background"] is not None:
        lines.append(
            f'  <rect id="document-background" width="{width}" height="{height}" '
            f'fill="{document["background"].upper()}"/>'
        )
    for layer in scene["layers"]:
        display = "" if layer["visible"] else ' display="none"'
        lines.append(
            f'  <g id="{escape(layer["id"], quote=True)}" '
            f'data-layer-name="{escape(layer["name"], quote=True)}"{display}>'
        )
        for item in objects_by_layer[layer["id"]]:
            lines.append("    " + _compile_object(item, palette))
        lines.append("  </g>")
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def _style_attributes(item: dict[str, Any], palette: dict[str, str]) -> str:
    style = item["style"]
    attrs = {
        "fill": _resolve_paint(style["fill"], palette, name="fill"),
        "stroke": _resolve_paint(style["stroke"], palette, name="stroke"),
        "stroke-width": _format_number(style["stroke_width"]),
        "opacity": _format_number(style["opacity"]),
    }
    if "line_cap" in style:
        attrs["stroke-linecap"] = style["line_cap"]
    if "line_join" in style:
        attrs["stroke-linejoin"] = style["line_join"]
    return " ".join(f'{key}="{escape(value, quote=True)}"' for key, value in attrs.items())


def _compile_object(item: dict[str, Any], palette: dict[str, str]) -> str:
    object_id = escape(item["id"], quote=True)
    style = _style_attributes(item, palette)
    object_type = item["type"]
    if object_type == "rect":
        rx = f' rx="{_format_number(item["rx"])}"' if "rx" in item else ""
        return f'<rect id="{object_id}" x="{_format_number(item["x"])}" y="{_format_number(item["y"])}" width="{_format_number(item["width"])}" height="{_format_number(item["height"])}"{rx} {style}/>'
    if object_type == "circle":
        return f'<circle id="{object_id}" cx="{_format_number(item["cx"])}" cy="{_format_number(item["cy"])}" r="{_format_number(item["r"])}" {style}/>'
    if object_type == "ellipse":
        return f'<ellipse id="{object_id}" cx="{_format_number(item["cx"])}" cy="{_format_number(item["cy"])}" rx="{_format_number(item["rx_radius"])}" ry="{_format_number(item["ry_radius"])}" {style}/>'
    if object_type == "line":
        return f'<line id="{object_id}" x1="{_format_number(item["x1"])}" y1="{_format_number(item["y1"])}" x2="{_format_number(item["x2"])}" y2="{_format_number(item["y2"])}" {style}/>'
    if object_type == "polygon":
        points = " ".join(f'{_format_number(point[0])},{_format_number(point[1])}' for point in item["points"])
        return f'<polygon id="{object_id}" points="{points}" {style}/>'
    if object_type == "path":
        path_data = []
        for command in item["commands"]:
            op = command["op"]
            if op in {"M", "L"}:
                path_data.append(f'{op} {_format_number(command["x"])} {_format_number(command["y"])}')
            elif op == "C":
                path_data.append(
                    f'C {_format_number(command["x1"])} {_format_number(command["y1"])} '
                    f'{_format_number(command["x2"])} {_format_number(command["y2"])} '
                    f'{_format_number(command["x"])} {_format_number(command["y"])}'
                )
            else:
                path_data.append("Z")
        return f'<path id="{object_id}" d="{" ".join(path_data)}" {style}/>'
    anchor = item.get("text_anchor", "start")
    return (
        f'<text id="{object_id}" x="{_format_number(item["x"])}" y="{_format_number(item["y"])}" '
        f'font-family="{escape(item["font_family"], quote=True)}" '
        f'font-size="{_format_number(item["font_size"])}" text-anchor="{anchor}" {style}>'
        f'{escape(item["text"])}</text>'
    )


def vector_scene_summary(scene: dict[str, Any]) -> dict[str, Any]:
    failures = validate_vector_scene(scene)
    return sanitize(
        {
            "ok": not failures,
            "scene_id": scene.get("scene_id"),
            "layer_count": len(scene.get("layers", [])),
            "object_count": len(scene.get("objects", [])),
            "object_types": sorted(
                {
                    item["type"]
                    for item in scene.get("objects", [])
                    if isinstance(item, dict) and isinstance(item.get("type"), str)
                }
            ),
            "failures": failures,
            "writes_files": False,
        }
    )
