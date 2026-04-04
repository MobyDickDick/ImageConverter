"""Extracted scalar/radius optimization helpers for imageCompositeConverter."""

from __future__ import annotations

import random


class ScalarRng:
    def __init__(self, seed: int) -> None:
        self._rng = random.Random(int(seed))

    def uniform(self, low: float, high: float) -> float:
        return float(self._rng.uniform(float(low), float(high)))

    def normal(self, mean: float, sigma: float) -> float:
        return float(self._rng.gauss(float(mean), float(sigma)))


def clipScalarImpl(value: float, low: float, high: float) -> float:
    """Return value clamped to ``[low, high]`` with ``numpy.clip`` scalar semantics."""
    lo = float(low)
    hi = float(high)
    # Mirror numpy.clip behaviour for inverted bounds (a_min > a_max):
    # any scalar collapses to the supplied upper bound.
    if lo > hi:
        return hi
    v = float(value)
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


def makeRngImpl(seed: int, *, np_module):
    if np_module is not None:
        return np_module.random.default_rng(int(seed))
    return ScalarRng(int(seed))


def argminIndexImpl(values: list[float]) -> int:
    return min(range(len(values)), key=lambda i: float(values[i]))


def snapIntPxImpl(value: float, minimum: float = 1.0) -> float:
    return float(max(int(round(float(minimum))), int(round(float(value)))))


def maxCircleRadiusInsideCanvasImpl(cx: float, cy: float, w: int, h: int, stroke: float = 0.0) -> float:
    """Return the largest circle radius that stays inside the SVG viewport."""
    if w <= 0 or h <= 0:
        return 1.0
    edge_margin = min(float(cx), float(w) - float(cx), float(cy), float(h) - float(cy))
    return float(max(1.0, edge_margin - (max(0.0, float(stroke)) / 2.0)))


def isCircleWithTextImpl(params: dict) -> bool:
    """Return True when the badge encodes a circle-with-text shape."""
    return bool(params.get("circle_enabled", True)) and bool(params.get("draw_text", False))


def applyCircleTextWidthConstraintImpl(params: dict, radius: float, w: int) -> float:
    """Enforce CircleWithText constraint: 2 * radius < image width."""
    if not isCircleWithTextImpl(params):
        return float(radius)
    # Keep a tiny strict margin so the optimized radius remains strictly below w/2.
    width_cap = (float(w) / 2.0) - 1e-3
    return float(min(float(radius), width_cap))


def applyCircleTextRadiusFloorImpl(params: dict, radius: float, *, text_bbox_fn) -> float:
    """Enforce CircleWithText lower bound: radius must exceed half text width."""
    if not isCircleWithTextImpl(params):
        return float(radius)
    x1, _y1, x2, _y2 = text_bbox_fn(params)
    text_width = max(0.0, float(x2) - float(x1))
    if text_width <= 0.0:
        return float(radius)
    # Keep strict inequality: radius > (text_width / 2).
    lower_bound = (text_width / 2.0) + 1e-3
    return float(max(float(radius), lower_bound))


def clampCircleInsideCanvasImpl(
    params: dict,
    w: int,
    h: int,
    *,
    text_bbox_fn,
) -> dict:
    """Clamp circle center/radius so no part of the ring exceeds the viewport."""
    p = dict(params)
    if not p.get("circle_enabled", True):
        return p
    if "cx" not in p or "cy" not in p or "r" not in p:
        return p

    cx = float(max(0.0, min(float(w), float(p.get("cx", 0.0)))))
    cy = float(max(0.0, min(float(h), float(p.get("cy", 0.0)))))
    stroke = float(p.get("stroke_circle", 0.0))
    max_r = maxCircleRadiusInsideCanvasImpl(cx, cy, w, h, stroke)
    max_r = applyCircleTextWidthConstraintImpl(p, max_r, w)
    min_r = float(
        max(
            1.0,
            float(p.get("min_circle_radius", 1.0)),
            float(p.get("circle_radius_lower_bound_px", 1.0)),
        )
    )
    min_r = applyCircleTextRadiusFloorImpl(p, min_r, text_bbox_fn=text_bbox_fn)
    if not bool(p.get("allow_circle_overflow", False)):
        min_r = min(min_r, max_r)

    p["cx"] = cx
    p["cy"] = cy
    if bool(p.get("allow_circle_overflow", False)):
        p["r"] = float(max(min_r, float(p.get("r", min_r))))
    else:
        p["r"] = float(max(min_r, min(max_r, float(p.get("r", min_r)))))
    return p
