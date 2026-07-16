"""Sequential Geometry-IR optimization helpers.

The optimizer is intentionally renderer-agnostic: callers provide a renderer and
an error function, while this module enforces the PR-R3 contract that IR elements
are fitted one after another and only strictly improving candidates are accepted.
"""

from __future__ import annotations

import copy
from collections.abc import Callable, Iterable
from typing import Any

GeometryIr = list[dict[str, object]]
RenderFn = Callable[[GeometryIr], object]
ErrorFn = Callable[[object], float]
CandidateProvider = Callable[
    [dict[str, object], GeometryIr, int], Iterable[dict[str, object]]
]


def _element_name(element: dict[str, object]) -> str:
    return str(element.get("id") or element.get("kind") or "unknown")


def _clone_ir(geometry_ir: GeometryIr) -> GeometryIr:
    return copy.deepcopy(geometry_ir)


def _with_element(
    geometry_ir: GeometryIr, step_index: int, element: dict[str, object]
) -> GeometryIr:
    candidate_ir = _clone_ir(geometry_ir)
    candidate_ir[step_index] = copy.deepcopy(element)
    return candidate_ir


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _parse_percent_offset(value: object) -> float | None:
    """Return a normalized gradient offset for percentage-style SVG stops."""

    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if not stripped.endswith("%"):
        return None
    try:
        return _clamp01(float(stripped[:-1]) / 100.0)
    except ValueError:
        return None


def _format_percent_offset(value: float) -> str:
    """Format a normalized gradient offset as stable SVG percentage text."""

    percent = _clamp01(value) * 100.0
    if abs(percent - round(percent)) < 1e-9:
        return f"{int(round(percent))}%"
    return f"{percent:.4f}".rstrip("0").rstrip(".") + "%"


def _default_candidate_provider(
    element: dict[str, object], _current_ir: GeometryIr, _step_index: int
) -> Iterable[dict[str, object]]:
    """Yield conservative local parameter probes for one IR element.

    The default provider is deliberately small and deterministic. Production
    callers can pass a richer provider, while tests can pass exact mock
    candidates. The current element is yielded first so a non-improving step can
    be logged without changing the IR.
    """

    yield copy.deepcopy(element)

    bbox = element.get("bbox")
    if isinstance(bbox, list) and len(bbox) == 4:
        coarse_delta = 0.02
        fine_deltas = (
            (0.000625, 0.00125, 0.0025, 0.005, 0.01)
            if element.get("kind") in {"ColorPatch", "RectBorder"}
            else (coarse_delta,)
        )
        probes = []
        for idx in range(4):
            for delta in (
                -coarse_delta,
                *(-d for d in fine_deltas),
                *fine_deltas,
                coarse_delta,
            ):
                if (idx, delta) not in probes:
                    probes.append((idx, delta))
        for idx, delta in probes:
            candidate = copy.deepcopy(element)
            candidate_bbox = [float(v) for v in bbox]
            candidate_bbox[idx] = _clamp01(candidate_bbox[idx] + delta)
            if candidate_bbox[2] > 0.01 and candidate_bbox[3] > 0.01:
                candidate["bbox"] = candidate_bbox
                yield candidate

    if "stroke_width" in element:
        stroke_width = max(0.001, float(element.get("stroke_width", 0.01)))
        for factor in (0.85, 1.15):
            candidate = copy.deepcopy(element)
            candidate["stroke_width"] = max(0.001, stroke_width * factor)
            yield candidate

        if element.get("kind") == "PolygonPath":
            for delta in (
                -0.01,
                -0.005,
                -0.0025,
                -0.00125,
                -0.000625,
                -0.0003125,
                -0.00015625,
                -0.000078125,
                -0.0000390625,
                -0.00001953125,
                -0.000009765625,
                -0.0000048828125,
                -0.00000244140625,
                -0.000001220703125,
                -0.0000006103515625,
                -0.00000030517578125,
                -0.000000152587890625,
                0.000000152587890625,
                0.00000030517578125,
                0.0000006103515625,
                0.000001220703125,
                0.00000244140625,
                0.0000048828125,
                0.000009765625,
                0.00001953125,
                0.0000390625,
                0.000078125,
                0.00015625,
                0.0003125,
                0.000625,
                0.00125,
                0.0025,
                0.005,
                0.01,
            ):
                candidate = copy.deepcopy(element)
                candidate["stroke_width"] = max(0.001, stroke_width + delta)
                yield candidate

        if element.get("kind") in {"RectBorder", "HorizontalRule", "VerticalRule"}:
            for delta in (
                -0.005,
                -0.0025,
                -0.00125,
                -0.000625,
                -0.0003125,
                -0.00015625,
                -0.000078125,
                -0.0000390625,
                -0.00001953125,
                -0.000009765625,
                -0.0000048828125,
                -0.00000244140625,
                -0.000001220703125,
                -0.0000006103515625,
                -0.00000030517578125,
                0.00000030517578125,
                0.0000006103515625,
                0.000001220703125,
                0.00000244140625,
                0.0000048828125,
                0.000009765625,
                0.00001953125,
                0.0000390625,
                0.000078125,
                0.00015625,
                0.0003125,
                0.000625,
                0.00125,
                0.0025,
                0.005,
            ):
                candidate = copy.deepcopy(element)
                candidate["stroke_width"] = max(0.001, stroke_width + delta)
                yield candidate

    points = element.get("points")
    if element.get("kind") == "PolygonPath" and isinstance(points, list) and points:
        valid_points = [
            [float(point[0]), float(point[1])]
            for point in points
            if isinstance(point, list) and len(point) >= 2
        ]
        if len(valid_points) == len(points):
            for coord_index in (0, 1):
                for delta in (
                    -0.04,
                    -0.02,
                    -0.01,
                    -0.005,
                    -0.0025,
                    -0.00125,
                    -0.000625,
                    -0.0003125,
                    -0.00015625,
                    -0.000078125,
                    0.000078125,
                    0.00015625,
                    0.0003125,
                    0.000625,
                    0.00125,
                    0.0025,
                    0.005,
                    0.01,
                    0.02,
                    0.04,
                ):
                    shifted_points = []
                    for point in valid_points:
                        shifted_point = list(point)
                        shifted_point[coord_index] = _clamp01(
                            shifted_point[coord_index] + delta
                        )
                        shifted_points.append(shifted_point)
                    if shifted_points == valid_points:
                        continue
                    candidate = copy.deepcopy(element)
                    candidate["points"] = shifted_points
                    yield candidate

        for point_index, point in enumerate(points):
            if not (isinstance(point, list) and len(point) >= 2):
                continue
            for coord_index in (0, 1):
                for delta in (
                    -0.02,
                    -0.01,
                    -0.005,
                    -0.0025,
                    -0.00125,
                    -0.000625,
                    -0.0003125,
                    -0.00015625,
                    -0.000078125,
                    -0.0000390625,
                    -0.00001953125,
                    -0.000009765625,
                    -0.0000048828125,
                    -0.00000244140625,
                    -0.000001220703125,
                    -0.0000006103515625,
                    -0.00000030517578125,
                    -0.000000152587890625,
                    0.000000152587890625,
                    0.00000030517578125,
                    0.0000006103515625,
                    0.000001220703125,
                    0.00000244140625,
                    0.0000048828125,
                    0.000009765625,
                    0.00001953125,
                    0.0000390625,
                    0.000078125,
                    0.00015625,
                    0.0003125,
                    0.000625,
                    0.00125,
                    0.0025,
                    0.005,
                    0.01,
                    0.02,
                ):
                    candidate = copy.deepcopy(element)
                    candidate_points = candidate.get("points")
                    if not isinstance(candidate_points, list):
                        continue
                    candidate_point = candidate_points[point_index]
                    if not (
                        isinstance(candidate_point, list) and len(candidate_point) >= 2
                    ):
                        continue
                    candidate_point[coord_index] = _clamp01(
                        float(candidate_point[coord_index]) + delta
                    )
                    candidate["points"] = candidate_points
                    yield candidate

        linecap = str(element.get("linecap", "butt")).strip().lower()
        for candidate_linecap in ("butt", "round", "square"):
            if candidate_linecap == linecap:
                continue
            candidate = copy.deepcopy(element)
            candidate["linecap"] = candidate_linecap
            yield candidate

        linejoin = str(element.get("linejoin", "round")).strip().lower()
        for candidate_linejoin in ("round", "miter", "bevel"):
            if candidate_linejoin == linejoin:
                continue
            candidate = copy.deepcopy(element)
            candidate["linejoin"] = candidate_linejoin
            yield candidate

        stroke_opacity = float(element.get("stroke_opacity", 1.0))
        for candidate_opacity in (0.65, 0.75, 0.85, 0.95, 1.0):
            if abs(candidate_opacity - stroke_opacity) < 1e-9:
                continue
            candidate = copy.deepcopy(element)
            candidate["stroke_opacity"] = candidate_opacity
            yield candidate

        fill_opacity = float(element.get("fill_opacity", 1.0))
        for candidate_opacity in (0.65, 0.75, 0.85, 0.95, 1.0):
            if abs(candidate_opacity - fill_opacity) < 1e-9:
                continue
            candidate = copy.deepcopy(element)
            candidate["fill_opacity"] = candidate_opacity
            yield candidate

        stroke_palette = (
            "#6f6f6f",
            "#7f7f7f",
            "#8a8a8a",
            "#969696",
            "#a0a0a0",
            "#176f28",
            "#2f8f3d",
            "#3c9f44",
            "#43ad49",
            "#68b868",
            "#8fc78e",
            "#c8d0c3",
        )
        stroke = str(element.get("stroke", "")).strip().lower()
        if stroke not in {"", "none", "transparent"}:
            for color in stroke_palette:
                if color == stroke:
                    continue
                candidate = copy.deepcopy(element)
                candidate["stroke"] = color
                yield candidate

        stroke_gradient = element.get("stroke_gradient")
        if isinstance(stroke_gradient, dict) and isinstance(
            stroke_gradient.get("stops"), list
        ):
            for stop_index, stop in enumerate(stroke_gradient["stops"]):
                if not isinstance(stop, dict):
                    continue
                stop_color = str(stop.get("color", "")).strip().lower()
                if stop_color in {"", "none", "transparent"}:
                    continue
                for color in stroke_palette:
                    if color == stop_color:
                        continue
                    candidate = copy.deepcopy(element)
                    candidate_gradient = candidate.get("stroke_gradient")
                    if not isinstance(candidate_gradient, dict) or not isinstance(
                        candidate_gradient.get("stops"), list
                    ):
                        continue
                    candidate_stops = candidate_gradient["stops"]
                    if stop_index >= len(candidate_stops) or not isinstance(
                        candidate_stops[stop_index], dict
                    ):
                        continue
                    candidate_stops[stop_index]["color"] = color
                    yield candidate
                stop_offset = _parse_percent_offset(stop.get("offset"))
                if stop_offset is None:
                    continue
                for delta in (
                    -0.10,
                    -0.05,
                    -0.025,
                    -0.0125,
                    -0.00625,
                    -0.003125,
                    -0.0015625,
                    -0.00078125,
                    -0.000390625,
                    -0.0001953125,
                    -0.00009765625,
                    -0.000048828125,
                    -0.0000244140625,
                    -0.00001220703125,
                    -0.000006103515625,
                    -0.0000030517578125,
                    -0.00000152587890625,
                    -0.000000762939453125,
                    -0.0000003814697265625,
                    -0.00000019073486328125,
                    0.00000019073486328125,
                    0.0000003814697265625,
                    0.000000762939453125,
                    0.00000152587890625,
                    0.0000030517578125,
                    0.000006103515625,
                    0.00001220703125,
                    0.0000244140625,
                    0.000048828125,
                    0.00009765625,
                    0.0001953125,
                    0.000390625,
                    0.00078125,
                    0.0015625,
                    0.003125,
                    0.00625,
                    0.0125,
                    0.025,
                    0.05,
                    0.10,
                ):
                    candidate_offset = _clamp01(stop_offset + delta)
                    if abs(candidate_offset - stop_offset) < 1e-9:
                        continue
                    candidate = copy.deepcopy(element)
                    candidate_gradient = candidate.get("stroke_gradient")
                    if not isinstance(candidate_gradient, dict) or not isinstance(
                        candidate_gradient.get("stops"), list
                    ):
                        continue
                    candidate_stops = candidate_gradient["stops"]
                    if stop_index >= len(candidate_stops) or not isinstance(
                        candidate_stops[stop_index], dict
                    ):
                        continue
                    candidate_stops[stop_index]["offset"] = _format_percent_offset(
                        candidate_offset
                    )
                    yield candidate

        fill = str(element.get("fill", "")).strip().lower()
        if fill not in {"", "none", "transparent"}:
            for color in (
                "#d9001b",
                "#e0001f",
                "#e10821",
                "#e3162a",
                "#f00020",
                "#0f557a",
                "#1a5d83",
                "#24678d",
                "#2e7198",
                "#367aa1",
            ):
                if color == fill:
                    continue
                candidate = copy.deepcopy(element)
                candidate["fill"] = color
                yield candidate

    if element.get("kind") in {"PlusGlyph", "MinusGlyph"}:
        for delta in (-0.02, 0.02):
            candidate = copy.deepcopy(element)
            candidate["dy"] = float(element.get("dy", 0.0)) + delta
            yield candidate

    if element.get("kind") in {"ColorPatch", "RectBorder"}:
        fill_opacity = float(element.get("fill_opacity", 1.0))
        for candidate_opacity in (
            0.75,
            0.85,
            0.9,
            0.9125,
            0.91328125,
            0.9140625,
            0.91484375,
            0.915625,
            0.9171875,
            0.91875,
            0.925,
            0.93125,
            0.9375,
            0.94375,
            0.95,
            0.95625,
            0.9625,
            0.96875,
            0.975,
            0.98125,
            0.98203125,
            0.982421875,
            0.9826171875,
            0.98271484375,
            0.982763671875,
            0.9827880859375,
            0.98280029296875,
            0.982806396484375,
            0.9828094482421875,
            0.98281097412109375,
            0.982811737060546875,
            0.9828125,
            0.98291015625,
            0.9830078125,
            0.983203125,
            0.98359375,
            0.984375,
            0.9859375,
            0.9875,
            1.0,
        ):
            if abs(candidate_opacity - fill_opacity) < 1e-9:
                continue
            candidate = copy.deepcopy(element)
            candidate["fill_opacity"] = candidate_opacity
            yield candidate

        stroke_opacity = float(element.get("stroke_opacity", 1.0))
        for candidate_opacity in (
            0.75,
            0.85,
            0.9,
            0.9125,
            0.91328125,
            0.9140625,
            0.91484375,
            0.915625,
            0.9171875,
            0.91875,
            0.925,
            0.93125,
            0.9375,
            0.94375,
            0.95,
            0.95625,
            0.9625,
            0.96875,
            0.975,
            0.98125,
            0.98203125,
            0.982421875,
            0.9826171875,
            0.98271484375,
            0.9828125,
            0.982813262939453125,
            0.98281402587890625,
            0.9828155517578125,
            0.982818603515625,
            0.98282470703125,
            0.9828369140625,
            0.982861328125,
            0.98291015625,
            0.9830078125,
            0.983203125,
            0.98359375,
            0.984375,
            0.9859375,
            0.9875,
            1.0,
        ):
            if abs(candidate_opacity - stroke_opacity) < 1e-9:
                continue
            candidate = copy.deepcopy(element)
            candidate["stroke_opacity"] = candidate_opacity
            yield candidate

    if element.get("kind") in {"ColorPatch", "RectBorder"} and isinstance(
        element.get("fill"), str
    ):
        fill = str(element.get("fill", "")).strip().lower()
        if fill not in {"", "none", "transparent"}:
            for color in (
                "#f0f0f0",
                "#e8e8e8",
                "#e0e0e0",
                "#d8d8d8",
                "#d0d0d0",
                "#c8c8c8",
                "#c0c0c0",
                "#b8c8d0",
                "#b1c1cc",
                "#d8ead2",
                "#d0e4ca",
                "#c8dcc2",
                "#bfd4ba",
                "#f2b8b4",
                "#f2b8b5",
                "#f2b9b5",
                "#f3b9b5",
                "#f2b9b6",
                "#f3b9b6",
                "#f2b9b7",
                "#f2bab6",
                "#f2bab7",
                "#f2bab8",
                "#f3bab8",
                "#f3bab9",
                "#f3baba",
                "#f3babb",
                "#f3babc",
                "#f2bbb7",
                "#f2bbb8",
                "#f2bcb8",
                "#f3bdb9",
                "#f3beb9",
                "#f3bfba",
                "#f3c0bc",
                "#f4c1bd",
                "#f4c2be",
                "#f4c3bf",
                "#f4c4c0",
            ):
                if color == fill:
                    continue
                candidate = copy.deepcopy(element)
                candidate["fill"] = color
                yield candidate

    if element.get("kind") == "RectBorder" and isinstance(element.get("stroke"), str):
        stroke = str(element.get("stroke", "")).strip().lower()
        if stroke not in {"", "none", "transparent"}:
            for color in (
                "#606060",
                "#6f6f6f",
                "#7f7f7f",
                "#8a8a8a",
                "#969696",
                "#a0a0a0",
                "#adadad",
                "#b8b8b8",
            ):
                if color == stroke:
                    continue
                candidate = copy.deepcopy(element)
                candidate["stroke"] = color
                yield candidate


def evaluateGeometryIrImpl(
    geometry_ir: GeometryIr, *, render_fn: RenderFn, error_fn: ErrorFn
) -> float:
    """Render and score a Geometry-IR chain."""

    return float(error_fn(render_fn(_clone_ir(geometry_ir))))


def optimizeGeometryIrSequentiallyImpl(
    geometry_ir: GeometryIr,
    *,
    render_fn: RenderFn,
    error_fn: ErrorFn,
    candidate_provider: CandidateProvider | None = None,
    min_improvement: float = 1e-9,
) -> dict[str, Any]:
    """Optimize a Geometry-IR chain element by element.

    For each IR element all candidates are scored against the current accepted
    chain. Only the best strictly improving candidate is committed before moving
    to the next element; regressions and ties are rejected. The returned step log
    uses the stable PR-R3 fields ``step_index``, ``element``, ``best_delta`` and
    ``accepted``.
    """

    current_ir = _clone_ir(geometry_ir)
    provider = candidate_provider or _default_candidate_provider
    current_error = evaluateGeometryIrImpl(
        current_ir, render_fn=render_fn, error_fn=error_fn
    )
    initial_error = current_error
    steps: list[dict[str, object]] = []

    for step_index, element in enumerate(list(current_ir)):
        error_before = current_error
        best_error = current_error
        best_ir = current_ir

        for candidate_element in provider(
            copy.deepcopy(element), _clone_ir(current_ir), step_index
        ):
            probe_ir = _with_element(current_ir, step_index, candidate_element)
            candidate_error = evaluateGeometryIrImpl(
                probe_ir, render_fn=render_fn, error_fn=error_fn
            )
            if candidate_error < best_error - min_improvement:
                best_error = candidate_error
                best_ir = probe_ir

        accepted = best_error < error_before - min_improvement
        if accepted:
            current_ir = best_ir
            current_error = best_error

        steps.append(
            {
                "step_index": step_index,
                "element": _element_name(element),
                "best_delta": float(error_before - best_error) if accepted else 0.0,
                "accepted": accepted,
                "error_before": float(error_before),
                "error_after": float(current_error),
            }
        )

    return {
        "mode": "elementwise_geometry_ir",
        "geometry_ir": current_ir,
        "initial_error": float(initial_error),
        "final_error": float(current_error),
        "steps": steps,
    }


def selectGeometryIrForRenderingImpl(params: dict[str, Any]) -> GeometryIr:
    """Return the IR chain that should be rendered by the standard path.

    Optimized elementwise results take precedence. A one-shot chain is accepted
    only when the caller explicitly marks it as an emergency mode, preventing
    implicit direct-SVG/one-shot behavior from becoming the default again.
    """

    optimized = params.get("optimized_geometry_ir")
    if isinstance(optimized, list) and optimized:
        params["geometry_phase_mode"] = "elementwise_geometry_ir"
        return optimized

    geometry_ir = params.get("geometry_ir")
    if isinstance(geometry_ir, list) and geometry_ir:
        params.setdefault("geometry_phase_mode", "elementwise_geometry_ir")
        return geometry_ir

    emergency_ir = params.get("one_shot_emergency_geometry_ir")
    if (
        params.get("allow_one_shot_emergency") is True
        and isinstance(emergency_ir, list)
        and emergency_ir
    ):
        params["geometry_phase_mode"] = "one_shot_emergency"
        return emergency_ir

    params.setdefault("geometry_phase_mode", "no_geometry_ir")
    return []


def _transform_point(
    point: list[object],
    *,
    translate_x: float,
    translate_y: float,
    scale_x: float,
    scale_y: float,
) -> list[float]:
    return [
        0.5 + (float(point[0]) - 0.5) * scale_x + translate_x,
        0.5 + (float(point[1]) - 0.5) * scale_y + translate_y,
    ]


def transformGeometryIrImpl(
    geometry_ir: GeometryIr,
    *,
    translate_x: float = 0.0,
    translate_y: float = 0.0,
    scale_x: float = 1.0,
    scale_y: float = 1.0,
    stroke_scale: float = 1.0,
) -> GeometryIr:
    """Apply a structure-preserving global registration transform to Geometry-IR.

    Coordinates remain normalized and may deliberately extend beyond ``0..1``;
    SVG clipping then handles symbols whose antialiased strokes touch an image
    edge.  Only documented geometry fields are transformed, so labels, colors,
    semantic IDs, and element ordering remain unchanged.
    """

    transformed = _clone_ir(geometry_ir)
    point_list_fields = ("points", "body_path", "connector", "blade_points")
    point_fields = ("center", "label_center")

    for element in transformed:
        for field in point_list_fields:
            points = element.get(field)
            if isinstance(points, list):
                element[field] = [
                    _transform_point(
                        point,
                        translate_x=translate_x,
                        translate_y=translate_y,
                        scale_x=scale_x,
                        scale_y=scale_y,
                    )
                    for point in points
                    if isinstance(point, list) and len(point) == 2
                ]

        body_paths = element.get("body_paths")
        if isinstance(body_paths, list):
            element["body_paths"] = [
                [
                    _transform_point(
                        point,
                        translate_x=translate_x,
                        translate_y=translate_y,
                        scale_x=scale_x,
                        scale_y=scale_y,
                    )
                    for point in path
                    if isinstance(point, list) and len(point) == 2
                ]
                for path in body_paths
                if isinstance(path, list)
            ]

        for field in point_fields:
            point = element.get(field)
            if isinstance(point, list) and len(point) == 2:
                element[field] = _transform_point(
                    point,
                    translate_x=translate_x,
                    translate_y=translate_y,
                    scale_x=scale_x,
                    scale_y=scale_y,
                )

        circle = element.get("circle")
        if isinstance(circle, list) and len(circle) == 3:
            center = _transform_point(
                circle[:2],
                translate_x=translate_x,
                translate_y=translate_y,
                scale_x=scale_x,
                scale_y=scale_y,
            )
            element["circle"] = [*center, float(circle[2]) * min(scale_x, scale_y)]

        for field in ("bbox", "body_bbox"):
            bbox = element.get(field)
            if isinstance(bbox, list) and len(bbox) == 4:
                origin = _transform_point(
                    bbox[:2],
                    translate_x=translate_x,
                    translate_y=translate_y,
                    scale_x=scale_x,
                    scale_y=scale_y,
                )
                element[field] = [
                    *origin,
                    float(bbox[2]) * scale_x,
                    float(bbox[3]) * scale_y,
                ]

        for field in ("stroke_width", "connector_width"):
            if field in element:
                element[field] = max(0.001, float(element[field]) * stroke_scale)
        if "font_size" in element:
            element["font_size"] = max(
                0.001,
                float(element["font_size"]) * min(scale_x, scale_y),
            )

    return transformed


def _gray_hex(value: float) -> str:
    gray = max(0, min(255, int(round(value))))
    return f"#{gray:02x}{gray:02x}{gray:02x}"


def _mutate_right_rotated_valve_parameter(
    geometry_ir: GeometryIr,
    *,
    parameter: str,
    delta: float,
) -> GeometryIr:
    """Adjust one topology-preserving parameter of the right-rotated valve glyph."""

    candidate = _clone_ir(geometry_ir)
    element = candidate[0]
    body_paths = element.get("body_paths")
    circle = element.get("circle")
    connector = element.get("connector")
    if not (
        isinstance(body_paths, list)
        and len(body_paths) == 3
        and all(isinstance(path, list) and len(path) == 3 for path in body_paths)
        and isinstance(circle, list)
        and len(circle) == 3
        and isinstance(connector, list)
        and len(connector) == 2
    ):
        return candidate

    if parameter == "circle_x":
        circle[0] = float(circle[0]) + delta
    elif parameter == "circle_y":
        circle[1] = float(circle[1]) + delta
    elif parameter == "circle_radius":
        circle[2] = max(0.02, float(circle[2]) + delta)
    elif parameter == "body_center_x":
        for path in body_paths:
            path[0][0] = float(path[0][0]) + delta
        connector[1][0] = float(connector[1][0]) + delta
    elif parameter == "body_center_y":
        for path in body_paths:
            path[0][1] = float(path[0][1]) + delta
        for point in connector:
            point[1] = float(point[1]) + delta
    elif parameter == "vertical_inner_x":
        body_paths[0][1][0] = float(body_paths[0][1][0]) + delta
        body_paths[1][1][0] = float(body_paths[1][1][0]) + delta
    elif parameter == "vertical_outer_x":
        body_paths[0][2][0] = float(body_paths[0][2][0]) + delta
        body_paths[1][2][0] = float(body_paths[1][2][0]) + delta
    elif parameter == "vertical_extent":
        for point in body_paths[0][1:]:
            point[1] = float(point[1]) + delta
        for point in body_paths[1][1:]:
            point[1] = float(point[1]) - delta
    elif parameter == "right_extent":
        body_paths[2][1][0] = float(body_paths[2][1][0]) + delta
        body_paths[2][2][0] = float(body_paths[2][2][0]) + delta
    elif parameter == "right_half_height":
        body_paths[2][1][1] = float(body_paths[2][1][1]) + delta
        body_paths[2][2][1] = float(body_paths[2][2][1]) - delta
    elif parameter == "connector_start_x":
        connector[0][0] = float(connector[0][0]) + delta
    elif parameter == "stroke_width":
        element["stroke_width"] = max(
            0.002, float(element.get("stroke_width", 0.04)) + delta
        )
    elif parameter == "connector_width":
        element["connector_width"] = max(
            0.002, float(element.get("connector_width", 0.075)) + delta
        )
    return candidate


def refineRightRotatedValveGeometryImpl(
    geometry_ir: GeometryIr,
    *,
    render_fn: RenderFn,
    error_fn: ErrorFn,
    min_improvement: float = 1e-9,
) -> dict[str, Any]:
    """Refine right-rotated valve geometry beyond a single global registration transform.

    A global transform cannot independently fit the handle and the three-way
    valve body.  This second phase retains the semantic topology and bilateral
    symmetry while fitting their relative geometry, line weights, and grayscale
    palette.  Every scale is exhausted until a complete pass finds no
    improvement; the previous fixed four-pass ceiling could stop while the same
    parameter was still improving.
    """

    current_ir = _clone_ir(geometry_ir)
    current_rendered = render_fn(current_ir)
    current_error = (
        float("inf") if current_rendered is None else float(error_fn(current_rendered))
    )
    initial_error = current_error
    steps: list[dict[str, object]] = []
    if (
        not current_ir
        or current_ir[0].get("kind") != "RightRotatedTopKelleThreeWayValveGlyph"
    ):
        return {
            "mode": "right_rotated_valve_geometry",
            "geometry_ir": current_ir,
            "rendered": current_rendered,
            "initial_error": initial_error,
            "final_error": current_error,
            "steps": steps,
        }

    parameters = (
        "circle_x",
        "circle_y",
        "circle_radius",
        "body_center_x",
        "body_center_y",
        "vertical_inner_x",
        "vertical_outer_x",
        "vertical_extent",
        "right_extent",
        "right_half_height",
        "connector_start_x",
        "stroke_width",
        "connector_width",
    )
    for stage_index, step in enumerate((0.08, 0.04, 0.02, 0.01, 0.005, 0.0025)):
        pass_index = 0
        while pass_index < 64:
            pass_improved = False
            for parameter in parameters:
                best_probe = None
                for direction in (-1.0, 1.0):
                    probe_ir = _mutate_right_rotated_valve_parameter(
                        current_ir,
                        parameter=parameter,
                        delta=direction * step,
                    )
                    probe_rendered = render_fn(probe_ir)
                    if probe_rendered is None:
                        continue
                    probe_error = float(error_fn(probe_rendered))
                    if probe_error < current_error - min_improvement and (
                        best_probe is None or probe_error < best_probe[0]
                    ):
                        best_probe = (
                            probe_error,
                            probe_ir,
                            probe_rendered,
                            direction * step,
                        )
                if best_probe is None:
                    continue
                previous_error = current_error
                current_error, current_ir, current_rendered, accepted_delta = best_probe
                steps.append(
                    {
                        "stage": stage_index,
                        "pass": pass_index,
                        "parameter": parameter,
                        "delta": float(accepted_delta),
                        "best_delta": float(previous_error - current_error),
                    }
                )
                pass_improved = True
            if not pass_improved:
                break
            pass_index += 1

    palette_defaults = {
        "body_fill": 215.0,
        "circle_fill": 250.0,
        "stroke": 150.0,
        "connector_stroke": 143.0,
    }
    for palette_key, initial_gray in palette_defaults.items():
        gray = initial_gray
        for stage_index, step in enumerate((40.0, 20.0, 10.0, 5.0, 2.0, 1.0)):
            while True:
                best_probe = None
                for direction in (-1.0, 1.0):
                    probe_gray = max(0.0, min(255.0, gray + direction * step))
                    probe_ir = _clone_ir(current_ir)
                    probe_ir[0][palette_key] = _gray_hex(probe_gray)
                    probe_rendered = render_fn(probe_ir)
                    if probe_rendered is None:
                        continue
                    probe_error = float(error_fn(probe_rendered))
                    if probe_error < current_error - min_improvement and (
                        best_probe is None or probe_error < best_probe[0]
                    ):
                        best_probe = (probe_error, probe_ir, probe_rendered, probe_gray)
                if best_probe is None:
                    break
                previous_error = current_error
                current_error, current_ir, current_rendered, gray = best_probe
                steps.append(
                    {
                        "stage": stage_index,
                        "parameter": palette_key,
                        "value": float(gray),
                        "best_delta": float(previous_error - current_error),
                    }
                )

    return {
        "mode": "right_rotated_valve_geometry",
        "geometry_ir": current_ir,
        "rendered": current_rendered,
        "initial_error": float(initial_error),
        "final_error": float(current_error),
        "steps": steps,
    }


def optimizeGeometryIrRegistrationImpl(
    geometry_ir: GeometryIr,
    *,
    render_fn: RenderFn,
    error_fn: ErrorFn,
    min_improvement: float = 1e-9,
) -> dict[str, Any]:
    """Fit semantic vector geometry to its source raster without changing meaning.

    A deterministic coarse-to-fine coordinate descent calibrates horizontal and
    vertical placement, scale, and line weight.  Every accepted probe must lower
    the caller-provided image error, making this safe for all Geometry-IR
    families rather than relying on family-specific coordinates.
    """

    parameter_names = (
        "translate_x",
        "translate_y",
        "scale_x",
        "scale_y",
        "stroke_scale",
    )
    parameters = [0.0, 0.0, 1.0, 1.0, 1.0]

    def evaluate(values: list[float]) -> tuple[float, GeometryIr, object]:
        candidate_ir = transformGeometryIrImpl(
            geometry_ir,
            **dict(zip(parameter_names, values)),
        )
        rendered = render_fn(candidate_ir)
        if rendered is None:
            return float("inf"), candidate_ir, rendered
        return float(error_fn(rendered)), candidate_ir, rendered

    current_error, current_ir, current_rendered = evaluate(parameters)
    initial_error = current_error
    accepted_steps: list[dict[str, object]] = []
    stages = (
        (0.08, 0.08, 0.15, 0.15, 0.25),
        (0.04, 0.04, 0.08, 0.08, 0.15),
        (0.02, 0.02, 0.04, 0.04, 0.08),
        (0.01, 0.01, 0.02, 0.02, 0.04),
    )

    for stage_index, stage_steps in enumerate(stages):
        pass_index = 0
        while pass_index < 64:
            pass_improved = False
            for parameter_index, step in enumerate(stage_steps):
                best_probe = None
                for direction in (-1.0, 1.0):
                    probe = list(parameters)
                    probe[parameter_index] += direction * step
                    if parameter_index >= 2 and probe[parameter_index] <= 0.2:
                        continue
                    probe_error, probe_ir, probe_rendered = evaluate(probe)
                    if probe_error < current_error - min_improvement and (
                        best_probe is None or probe_error < best_probe[0]
                    ):
                        best_probe = (probe_error, probe, probe_ir, probe_rendered)
                if best_probe is None:
                    continue
                previous_error = current_error
                current_error, parameters, current_ir, current_rendered = best_probe
                accepted_steps.append(
                    {
                        "stage": stage_index,
                        "parameter": parameter_names[parameter_index],
                        "value": float(parameters[parameter_index]),
                        "best_delta": float(previous_error - current_error),
                    }
                )
                pass_improved = True
            if not pass_improved:
                break
            pass_index += 1

    element_refinement = refineRightRotatedValveGeometryImpl(
        current_ir,
        render_fn=render_fn,
        error_fn=error_fn,
        min_improvement=min_improvement,
    )
    if float(element_refinement["final_error"]) < current_error - min_improvement:
        current_ir = element_refinement["geometry_ir"]
        current_rendered = element_refinement["rendered"]
        current_error = float(element_refinement["final_error"])

    generic_element_refinement = optimizeGeometryIrSequentiallyImpl(
        current_ir,
        render_fn=render_fn,
        error_fn=error_fn,
        min_improvement=min_improvement,
    )
    if (
        float(generic_element_refinement["final_error"])
        < current_error - min_improvement
    ):
        current_ir = generic_element_refinement["geometry_ir"]
        current_rendered = render_fn(current_ir)
        current_error = float(generic_element_refinement["final_error"])

    return {
        "mode": "geometry_ir_raster_registration",
        "geometry_ir": current_ir,
        "rendered": current_rendered,
        "initial_error": float(initial_error),
        "final_error": float(current_error),
        "parameters": dict(zip(parameter_names, parameters)),
        "steps": accepted_steps,
        "element_refinement": {
            key: value
            for key, value in element_refinement.items()
            if key not in {"geometry_ir", "rendered"}
        },
        "generic_element_refinement": {
            key: value
            for key, value in generic_element_refinement.items()
            if key not in {"geometry_ir", "rendered"}
        },
    }
