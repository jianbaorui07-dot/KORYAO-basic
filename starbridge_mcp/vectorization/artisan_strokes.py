from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np

from .presets import VectorPreset

Pixel = tuple[int, int]
Point = tuple[float, float]

_ORTHOGONAL_AND_DIAGONAL = (
    (-1, 0),
    (0, -1),
    (0, 1),
    (1, 0),
    (-1, -1),
    (-1, 1),
    (1, -1),
    (1, 1),
)


@dataclass(frozen=True)
class StrokeBatch:
    path_parts: tuple[str, ...]
    stroke_width: float
    bbox: tuple[int, int, int, int]
    representative_path: Any
    anchors: int
    raw_anchors: int
    control_points: int
    curve_segments: int
    line_segments: int
    corner_anchors: int
    smooth_anchors: int
    source_points: int
    length_px: float


def _format_coordinate(value: float) -> str:
    if math.isclose(value, round(value), abs_tol=0.0005):
        return str(int(round(value)))
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _point_text(point: Point) -> str:
    return f"{_format_coordinate(point[0])} {_format_coordinate(point[1])}"


def _interior_angle(previous: Point, current: Point, following: Point) -> float:
    first = (previous[0] - current[0], previous[1] - current[1])
    second = (following[0] - current[0], following[1] - current[1])
    first_length = math.hypot(*first)
    second_length = math.hypot(*second)
    if first_length == 0 or second_length == 0:
        return 0.0
    cosine = (first[0] * second[0] + first[1] * second[1]) / (first_length * second_length)
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def _unit(vector_x: float, vector_y: float) -> tuple[float, float]:
    length = math.hypot(vector_x, vector_y)
    if length == 0:
        return 0.0, 0.0
    return vector_x / length, vector_y / length


def _open_path(
    points: list[Point],
    *,
    corner_angle: float,
    smoothing: float,
) -> tuple[str, dict[str, Any]]:
    tangents: list[tuple[float, float]] = []
    smooth: list[bool] = []
    for index, current in enumerate(points):
        if index == 0:
            tangent = _unit(points[1][0] - current[0], points[1][1] - current[1])
            tangents.append(tangent)
            smooth.append(True)
        elif index == len(points) - 1:
            tangent = _unit(current[0] - points[index - 1][0], current[1] - points[index - 1][1])
            tangents.append(tangent)
            smooth.append(True)
        else:
            tangent = _unit(
                points[index + 1][0] - points[index - 1][0],
                points[index + 1][1] - points[index - 1][1],
            )
            tangents.append(tangent)
            smooth.append(
                _interior_angle(points[index - 1], current, points[index + 1]) >= corner_angle
            )

    minimum_x = min(point[0] for point in points)
    maximum_x = max(point[0] for point in points)
    minimum_y = min(point[1] for point in points)
    maximum_y = max(point[1] for point in points)
    commands = [f"M {_point_text(points[0])}"]
    sampled = [points[0]]
    curves = 0
    lines = 0
    controls = 0
    for index, current in enumerate(points[:-1]):
        following = points[index + 1]
        chord = math.dist(current, following)
        if chord > 1.0 and (smooth[index] or smooth[index + 1]):
            handle = chord * smoothing / 3.0
            control_1 = (
                max(minimum_x, min(maximum_x, current[0] + tangents[index][0] * handle)),
                max(minimum_y, min(maximum_y, current[1] + tangents[index][1] * handle)),
            )
            control_2 = (
                max(
                    minimum_x,
                    min(maximum_x, following[0] - tangents[index + 1][0] * handle),
                ),
                max(
                    minimum_y,
                    min(maximum_y, following[1] - tangents[index + 1][1] * handle),
                ),
            )
            commands.append(
                f"C {_point_text(control_1)} {_point_text(control_2)} {_point_text(following)}"
            )
            curves += 1
            controls += 2
            for sample_index in range(1, 9):
                t = sample_index / 8.0
                inverse = 1.0 - t
                sampled.append(
                    (
                        inverse**3 * current[0]
                        + 3 * inverse**2 * t * control_1[0]
                        + 3 * inverse * t**2 * control_2[0]
                        + t**3 * following[0],
                        inverse**3 * current[1]
                        + 3 * inverse**2 * t * control_1[1]
                        + 3 * inverse * t**2 * control_2[1]
                        + t**3 * following[1],
                    )
                )
        else:
            commands.append(f"L {_point_text(following)}")
            lines += 1
            sampled.append(following)
    return " ".join(commands), {
        "anchors": len(points),
        "control_points": controls,
        "curve_segments": curves,
        "line_segments": lines,
        "corner_anchors": sum(not value for value in smooth),
        "smooth_anchors": sum(smooth),
        "sampled_points": sampled,
    }


def _zhang_suen_thinning(mask: Any) -> tuple[Any, int]:
    image = np.pad((mask > 0).astype(np.uint8), 1)
    rounds = 0
    while True:
        removed = 0
        for phase in (0, 1):
            north = image[:-2, 1:-1]
            north_east = image[:-2, 2:]
            east = image[1:-1, 2:]
            south_east = image[2:, 2:]
            south = image[2:, 1:-1]
            south_west = image[2:, :-2]
            west = image[1:-1, :-2]
            north_west = image[:-2, :-2]
            center = image[1:-1, 1:-1]
            neighbor_count = (
                north + north_east + east + south_east + south + south_west + west + north_west
            )
            transitions = (
                ((north == 0) & (north_east == 1)).astype(np.uint8)
                + ((north_east == 0) & (east == 1))
                + ((east == 0) & (south_east == 1))
                + ((south_east == 0) & (south == 1))
                + ((south == 0) & (south_west == 1))
                + ((south_west == 0) & (west == 1))
                + ((west == 0) & (north_west == 1))
                + ((north_west == 0) & (north == 1))
            )
            if phase == 0:
                topology = (north * east * south == 0) & (east * south * west == 0)
            else:
                topology = (north * east * west == 0) & (north * south * west == 0)
            removable = (
                (center == 1)
                & (neighbor_count >= 2)
                & (neighbor_count <= 6)
                & (transitions == 1)
                & topology
            )
            count = int(np.count_nonzero(removable))
            center[removable] = 0
            removed += count
        rounds += 1
        if removed == 0:
            return image[1:-1, 1:-1], rounds


def _pixel_neighbors(pixel: Pixel, pixels: set[Pixel]) -> list[Pixel]:
    y, x = pixel
    neighbors: list[Pixel] = []
    for delta_y, delta_x in _ORTHOGONAL_AND_DIAGONAL:
        candidate = (y + delta_y, x + delta_x)
        if candidate not in pixels:
            continue
        if delta_y and delta_x and ((y, x + delta_x) in pixels or (y + delta_y, x) in pixels):
            continue
        neighbors.append(candidate)
    return neighbors


def _edge_key(first: Pixel, second: Pixel) -> tuple[Pixel, Pixel]:
    return (first, second) if first < second else (second, first)


def _graph_paths(skeleton: Any) -> tuple[list[list[Point]], dict[str, int]]:
    pixels = {(int(y), int(x)) for y, x in zip(*np.nonzero(skeleton), strict=True)}
    neighbors = {pixel: _pixel_neighbors(pixel, pixels) for pixel in pixels}
    node_pixels = {pixel for pixel, values in neighbors.items() if len(values) != 2}
    unseen = set(node_pixels)
    components: list[list[Pixel]] = []
    node_id: dict[Pixel, int] = {}
    for seed in sorted(node_pixels):
        if seed not in unseen:
            continue
        unseen.remove(seed)
        stack = [seed]
        component = [seed]
        while stack:
            pixel = stack.pop()
            for candidate in sorted(neighbors[pixel]):
                if candidate in unseen and candidate in node_pixels:
                    unseen.remove(candidate)
                    stack.append(candidate)
                    component.append(candidate)
        component_id = len(components)
        components.append(component)
        for pixel in component:
            node_id[pixel] = component_id
    centers = [
        (
            sum(pixel[0] for pixel in component) / len(component),
            sum(pixel[1] for pixel in component) / len(component),
        )
        for component in components
    ]

    visited: set[tuple[Pixel, Pixel]] = set()
    paths: list[list[Point]] = []
    components_with_edges: set[int] = set()
    for component_id, component in enumerate(components):
        for pixel in sorted(component):
            for candidate in sorted(neighbors[pixel]):
                edge = _edge_key(pixel, candidate)
                if candidate in node_pixels or edge in visited:
                    continue
                components_with_edges.add(component_id)
                path: list[Point] = [centers[component_id]]
                previous = pixel
                current = candidate
                visited.add(edge)
                while current not in node_pixels:
                    path.append((float(current[0]), float(current[1])))
                    options = sorted(value for value in neighbors[current] if value != previous)
                    if not options:
                        break
                    following = options[0]
                    edge = _edge_key(current, following)
                    if edge in visited:
                        break
                    previous, current = current, following
                    visited.add(edge)
                if current in node_pixels:
                    path.append(centers[node_id[current]])
                if len(path) >= 2:
                    paths.append(path)

    for component_id, center in enumerate(centers):
        if component_id not in components_with_edges:
            paths.append([center, (center[0], center[1] + 0.05)])

    for start in sorted(pixels - node_pixels):
        for candidate in sorted(neighbors[start]):
            edge = _edge_key(start, candidate)
            if candidate in node_pixels or edge in visited:
                continue
            path = [(float(start[0]), float(start[1]))]
            previous = start
            current = candidate
            visited.add(edge)
            while current != start:
                path.append((float(current[0]), float(current[1])))
                options = sorted(value for value in neighbors[current] if value != previous)
                if not options:
                    break
                following = options[0]
                edge = _edge_key(current, following)
                if edge in visited and following != start:
                    break
                previous, current = current, following
                visited.add(edge)
            if len(path) >= 3:
                path.append(path[0])
                paths.append(path)
    return paths, {
        "skeleton_pixels": len(pixels),
        "junction_pixels": len(node_pixels),
        "junction_clusters": len(components),
    }


def _distance_width(path: list[Point], distance: Any, height: int, width: int) -> float:
    values: list[float] = []
    for y, x in path:
        pixel_y = max(0, min(height - 1, int(round(y))))
        pixel_x = max(0, min(width - 1, int(round(x))))
        values.append(float(distance[pixel_y, pixel_x]) * 2.0)
    raw_width = float(np.median(values)) - 0.65 if values else 1.0
    return max(1.0, min(7.0, round(raw_width * 2.0) / 2.0))


def _path_extent(path: list[Point]) -> float:
    return sum(math.dist(path[index - 1], path[index]) for index in range(1, len(path)))


def _endpoint_direction(path: list[Point], endpoint: int) -> tuple[float, float]:
    origin = path[0] if endpoint == 0 else path[-1]
    candidates = path[1:] if endpoint == 0 else reversed(path[:-1])
    fallback = (0.0, 0.0)
    for candidate in candidates:
        vector = (candidate[0] - origin[0], candidate[1] - origin[1])
        fallback = _unit(*vector)
        if math.hypot(*vector) >= 2.0:
            return fallback
    return fallback


def _endpoint_width(
    path: list[Point],
    endpoint: int,
    distance: Any,
    height: int,
    width: int,
) -> float:
    candidates = path[1:6] if endpoint == 0 else list(reversed(path[:-1]))[:5]
    if not candidates:
        candidates = [path[0 if endpoint == 0 else -1]]
    values = []
    for y, x in candidates:
        pixel_y = max(0, min(height - 1, int(round(y))))
        pixel_x = max(0, min(width - 1, int(round(x))))
        values.append(float(distance[pixel_y, pixel_x]) * 2.0 - 0.65)
    return max(1.0, float(np.median(values)))


def _stitch_paths(
    paths: list[list[Point]],
    distance: Any,
    height: int,
    width: int,
    *,
    maximum_deviation_degrees: float = 38.0,
    maximum_width_difference: float = 1.5,
) -> tuple[list[list[Point]], dict[str, Any]]:
    endpoint_data: dict[
        tuple[float, float],
        list[tuple[tuple[int, int], tuple[float, float], float, float]],
    ] = {}
    for path_index, path in enumerate(paths):
        extent = _path_extent(path)
        if len(path) < 2 or extent < 1.0 or path[0] == path[-1]:
            continue
        for endpoint in (0, 1):
            point = path[0] if endpoint == 0 else path[-1]
            key = (round(point[0], 6), round(point[1], 6))
            endpoint_data.setdefault(key, []).append(
                (
                    (path_index, endpoint),
                    _endpoint_direction(path, endpoint),
                    _endpoint_width(path, endpoint, distance, height, width),
                    extent,
                )
            )

    connections: dict[tuple[int, int], tuple[int, int]] = {}
    used_deviations: list[float] = []
    used_width_differences: list[float] = []
    junctions_considered = 0
    eligible_pairs = 0
    for entries in endpoint_data.values():
        if len(entries) < 2:
            continue
        junctions_considered += 1
        candidates: list[tuple[float, float, float, tuple[int, int], tuple[int, int]]] = []
        for first_index, first in enumerate(entries[:-1]):
            for second in entries[first_index + 1 :]:
                first_endpoint, first_direction, first_width, first_extent = first
                second_endpoint, second_direction, second_width, second_extent = second
                if first_endpoint[0] == second_endpoint[0]:
                    continue
                dot = (
                    first_direction[0] * second_direction[0]
                    + first_direction[1] * second_direction[1]
                )
                deviation = math.degrees(math.acos(max(-1.0, min(1.0, -dot))))
                width_difference = abs(first_width - second_width)
                if (
                    deviation <= maximum_deviation_degrees
                    and width_difference <= maximum_width_difference
                ):
                    eligible_pairs += 1
                    candidates.append(
                        (
                            deviation,
                            width_difference,
                            -min(first_extent, second_extent),
                            first_endpoint,
                            second_endpoint,
                        )
                    )
        used: set[tuple[int, int]] = set()
        for deviation, width_difference, _, first_endpoint, second_endpoint in sorted(candidates):
            if first_endpoint in used or second_endpoint in used:
                continue
            connections[first_endpoint] = second_endpoint
            connections[second_endpoint] = first_endpoint
            used.add(first_endpoint)
            used.add(second_endpoint)
            used_deviations.append(deviation)
            used_width_differences.append(width_difference)

    starts: list[tuple[int, int]] = []
    for path_index in range(len(paths)):
        if (path_index, 0) not in connections:
            starts.append((path_index, 0))
        elif (path_index, 1) not in connections:
            starts.append((path_index, 1))
    starts.extend((path_index, 0) for path_index in range(len(paths)))

    stitched: list[list[Point]] = []
    visited: set[int] = set()
    for path_index, entry_endpoint in starts:
        if path_index in visited:
            continue
        trail: list[Point] = []
        current_index = path_index
        current_endpoint = entry_endpoint
        while current_index not in visited:
            path = paths[current_index]
            oriented = path if current_endpoint == 0 else list(reversed(path))
            if trail and trail[-1] == oriented[0]:
                trail.extend(oriented[1:])
            else:
                trail.extend(oriented)
            visited.add(current_index)
            exit_endpoint = (current_index, 1 - current_endpoint)
            continuation = connections.get(exit_endpoint)
            if continuation is None or continuation[0] in visited:
                break
            current_index, current_endpoint = continuation
        if len(trail) >= 2:
            stitched.append(trail)

    return stitched, {
        "continuation_junctions_considered": junctions_considered,
        "continuation_eligible_pairs": eligible_pairs,
        "continuation_pairs": len(connections) // 2,
        "continuation_maximum_deviation_degrees": round(max(used_deviations, default=0.0), 4),
        "continuation_mean_deviation_degrees": round(
            sum(used_deviations) / len(used_deviations) if used_deviations else 0.0,
            4,
        ),
        "continuation_maximum_width_difference_px": round(
            max(used_width_differences, default=0.0), 4
        ),
        "continuation_deviation_limit_degrees": maximum_deviation_degrees,
        "continuation_width_difference_limit_px": maximum_width_difference,
    }


def _bbox(points: list[Point], width: int, height: int) -> tuple[int, int, int, int]:
    minimum_x = max(0, math.floor(min(point[0] for point in points)))
    minimum_y = max(0, math.floor(min(point[1] for point in points)))
    maximum_x = min(width, math.ceil(max(point[0] for point in points)))
    maximum_y = min(height, math.ceil(max(point[1] for point in points)))
    return minimum_x, minimum_y, max(1, maximum_x - minimum_x), max(1, maximum_y - minimum_y)


def _trace_paths(
    paths: list[list[Point]],
    binary: Any,
    distance: Any,
    preset: VectorPreset,
    batch_limit: int,
) -> tuple[tuple[StrokeBatch, ...], dict[str, Any]]:
    height, width = binary.shape
    rendered = np.zeros_like(binary)
    simplify_epsilon = max(0.8, min(1.5, preset.simplify_ratio * 90.0))
    grouped: dict[float, list[dict[str, Any]]] = {}
    raw_anchor_count = 0
    anchor_count = 0
    for raw_path in paths:
        coordinates = np.asarray(
            [(x + 0.5, y + 0.5) for y, x in raw_path], dtype=np.float32
        ).reshape((-1, 1, 2))
        approximation = cv2.approxPolyDP(coordinates, simplify_epsilon, False).reshape((-1, 2))
        points = [(float(x), float(y)) for x, y in approximation]
        if len(points) < 2:
            continue
        path_data, path_metrics = _open_path(
            points,
            corner_angle=preset.corner_angle,
            smoothing=min(0.72, preset.curve_smoothing),
        )
        sampled_points = path_metrics.pop("sampled_points")
        stroke_width = _distance_width(raw_path, distance, height, width)
        render_points = np.rint(np.asarray(sampled_points, dtype=np.float32)).astype(np.int32)
        cv2.polylines(
            rendered,
            [render_points.reshape((-1, 1, 2))],
            False,
            1,
            max(1, round(stroke_width)),
            cv2.LINE_8,
        )
        raw_anchor_count += len(raw_path)
        anchor_count += int(path_metrics["anchors"])
        grouped.setdefault(stroke_width, []).append(
            {
                "path_data": path_data,
                "metrics": path_metrics,
                "sampled_points": sampled_points,
                "raw_anchors": len(raw_path),
                "source_points": len(raw_path),
                "length_px": _path_extent(points),
            }
        )

    original = binary.astype(bool)
    predicted = rendered.astype(bool)
    intersection = int(np.count_nonzero(original & predicted))
    original_count = int(np.count_nonzero(original))
    predicted_count = int(np.count_nonzero(predicted))
    precision = intersection / predicted_count if predicted_count else 0.0
    recall = intersection / original_count if original_count else 0.0
    dice = (
        2.0 * intersection / (original_count + predicted_count)
        if original_count + predicted_count
        else 0.0
    )

    batches: list[StrokeBatch] = []
    for stroke_width in sorted(grouped):
        entries = grouped[stroke_width]
        for start in range(0, len(entries), batch_limit):
            batch = entries[start : start + batch_limit]
            all_points = [point for entry in batch for point in entry["sampled_points"]]
            box = _bbox(all_points, width, height)
            representative = np.asarray(batch[0]["sampled_points"], dtype=np.float32).reshape(
                (-1, 1, 2)
            )
            batches.append(
                StrokeBatch(
                    path_parts=tuple(str(entry["path_data"]) for entry in batch),
                    stroke_width=stroke_width,
                    bbox=box,
                    representative_path=representative,
                    anchors=sum(int(entry["metrics"]["anchors"]) for entry in batch),
                    raw_anchors=sum(int(entry["raw_anchors"]) for entry in batch),
                    control_points=sum(int(entry["metrics"]["control_points"]) for entry in batch),
                    curve_segments=sum(int(entry["metrics"]["curve_segments"]) for entry in batch),
                    line_segments=sum(int(entry["metrics"]["line_segments"]) for entry in batch),
                    corner_anchors=sum(int(entry["metrics"]["corner_anchors"]) for entry in batch),
                    smooth_anchors=sum(int(entry["metrics"]["smooth_anchors"]) for entry in batch),
                    source_points=sum(int(entry["source_points"]) for entry in batch),
                    length_px=sum(float(entry["length_px"]) for entry in batch),
                )
            )
    return tuple(batches), {
        "subpaths": sum(len(batch.path_parts) for batch in batches),
        "batches": len(batches),
        "raw_anchors": raw_anchor_count,
        "anchors": anchor_count,
        "control_points": sum(batch.control_points for batch in batches),
        "precision": precision,
        "recall": recall,
        "dice": dice,
        "simplify_epsilon": simplify_epsilon,
        "min_stroke_width": min((batch.stroke_width for batch in batches), default=0.0),
        "max_stroke_width": max((batch.stroke_width for batch in batches), default=0.0),
    }


def trace_centerline_batches(
    ink_mask: Any,
    preset: VectorPreset,
    *,
    batch_limit: int = 96,
) -> tuple[tuple[StrokeBatch, ...], dict[str, Any]]:
    height, width = ink_mask.shape
    binary = (ink_mask > 0).astype(np.uint8)
    skeleton, thinning_rounds = _zhang_suen_thinning(binary)
    raw_paths, graph_metrics = _graph_paths(skeleton)
    distance = cv2.distanceTransform(binary * 255, cv2.DIST_L2, 5)
    continued_paths, continuation_metrics = _stitch_paths(
        raw_paths,
        distance,
        height,
        width,
    )
    baseline_batches, baseline = _trace_paths(
        raw_paths,
        binary,
        distance,
        preset,
        batch_limit,
    )
    continued_batches, continued = _trace_paths(
        continued_paths,
        binary,
        distance,
        preset,
        batch_limit,
    )
    baseline_lengths = [_path_extent(path) for path in raw_paths]
    continued_lengths = [_path_extent(path) for path in continued_paths]
    baseline_mean_length = (
        sum(baseline_lengths) / len(baseline_lengths) if baseline_lengths else 0.0
    )
    continued_mean_length = (
        sum(continued_lengths) / len(continued_lengths) if continued_lengths else 0.0
    )
    mean_length_gain = (
        max(0.0, continued_mean_length / baseline_mean_length - 1.0)
        if baseline_mean_length
        else 0.0
    )
    baseline_total_length = sum(baseline_lengths)
    continued_total_length = sum(continued_lengths)
    length_preservation = (
        continued_total_length / baseline_total_length if baseline_total_length else 1.0
    )
    path_reduction = (
        max(0.0, 1.0 - continued["subpaths"] / baseline["subpaths"])
        if baseline["subpaths"]
        else 0.0
    )
    anchor_reduction = (
        max(0.0, 1.0 - continued["anchors"] / baseline["anchors"]) if baseline["anchors"] else 0.0
    )
    baseline_points = int(baseline["anchors"]) + int(baseline["control_points"])
    continued_points = int(continued["anchors"]) + int(continued["control_points"])
    point_reduction = max(0.0, 1.0 - continued_points / baseline_points) if baseline_points else 0.0
    batch_reduction = (
        max(0.0, 1.0 - continued["batches"] / baseline["batches"]) if baseline["batches"] else 0.0
    )
    rejection_reasons: list[str] = []
    if path_reduction < 0.15:
        rejection_reasons.append("path_reduction_below_15_percent")
    if anchor_reduction < 0.03:
        rejection_reasons.append("anchor_reduction_below_3_percent")
    if continued["batches"] > baseline["batches"]:
        rejection_reasons.append("edit_batch_count_increased")
    if not math.isclose(length_preservation, 1.0, rel_tol=0.0, abs_tol=0.0001):
        rejection_reasons.append("skeleton_length_not_preserved")
    if continued["precision"] < baseline["precision"] - 0.01:
        rejection_reasons.append("precision_regression_over_0_01")
    if continued["recall"] < baseline["recall"] - 0.015:
        rejection_reasons.append("recall_regression_over_0_015")
    if continued["dice"] < baseline["dice"] - 0.01:
        rejection_reasons.append("dice_regression_over_0_01")
    continuation_used = not rejection_reasons
    batches = continued_batches if continuation_used else baseline_batches
    selected = continued if continuation_used else baseline
    return batches, {
        **graph_metrics,
        **continuation_metrics,
        "thinning_rounds": thinning_rounds,
        "centerline_raw_paths": len(raw_paths),
        "centerline_subpaths": selected["subpaths"],
        "centerline_batches": selected["batches"],
        "centerline_raw_anchors": selected["raw_anchors"],
        "centerline_anchors": selected["anchors"],
        "centerline_simplify_epsilon": round(float(selected["simplify_epsilon"]), 4),
        "centerline_precision": round(float(selected["precision"]), 6),
        "centerline_recall": round(float(selected["recall"]), 6),
        "centerline_dice": round(float(selected["dice"]), 6),
        "centerline_min_stroke_width": selected["min_stroke_width"],
        "centerline_max_stroke_width": selected["max_stroke_width"],
        "continuation_candidate_used": continuation_used,
        "continuation_rejection_reasons": rejection_reasons,
        "continuation_baseline_subpaths": baseline["subpaths"],
        "continuation_candidate_subpaths": continued["subpaths"],
        "continuation_path_reduction_ratio": round(path_reduction, 4),
        "continuation_baseline_anchors": baseline["anchors"],
        "continuation_candidate_anchors": continued["anchors"],
        "continuation_anchor_reduction_ratio": round(anchor_reduction, 4),
        "continuation_baseline_points": baseline_points,
        "continuation_candidate_points": continued_points,
        "continuation_point_reduction_ratio": round(point_reduction, 4),
        "continuation_baseline_batches": baseline["batches"],
        "continuation_candidate_batches": continued["batches"],
        "continuation_batch_reduction_ratio": round(batch_reduction, 4),
        "continuation_baseline_mean_path_length_px": round(baseline_mean_length, 4),
        "continuation_candidate_mean_path_length_px": round(continued_mean_length, 4),
        "continuation_mean_path_length_gain_ratio": round(mean_length_gain, 4),
        "continuation_length_preservation_ratio": round(length_preservation, 6),
        "continuation_baseline_maximum_path_length_px": round(
            max(baseline_lengths, default=0.0), 4
        ),
        "continuation_candidate_maximum_path_length_px": round(
            max(continued_lengths, default=0.0), 4
        ),
        "continuation_precision_delta": round(
            float(continued["precision"] - baseline["precision"]), 6
        ),
        "continuation_recall_delta": round(float(continued["recall"] - baseline["recall"]), 6),
        "continuation_dice_delta": round(float(continued["dice"] - baseline["dice"]), 6),
    }
