from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class VerticalLineDetection:
    x_center: float
    y_top: float
    y_bottom: float
    length_px: float
    width_px: float
    angle_deg: float
    confidence: float


@dataclass(frozen=True)
class PrimitiveColorDetection:
    fill_rgb: tuple[int, int, int] | None
    stroke_rgb: tuple[int, int, int] | None
    fill_hex: str | None
    stroke_hex: str | None
    fill_confidence: float
    stroke_confidence: float


def detect_vertical_lines(
    image,
    *,
    canny_low: int = 50,
    canny_high: int = 150,
    hough_threshold: int = 35,
    min_length_px: int = 12,
    max_gap_px: int = 6,
    angle_tolerance_deg: float = 12.0,
) -> list[VerticalLineDetection]:
    """Detect near-vertical line segments using Canny + Probabilistic Hough transform."""
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError("detect_vertical_lines requires numpy and opencv-python") from exc

    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    edges = cv2.Canny(gray, canny_low, canny_high)
    segments = cv2.HoughLinesP(edges, 1, np.pi / 180, hough_threshold, minLineLength=min_length_px, maxLineGap=max_gap_px)
    if segments is None:
        return []

    detections: list[VerticalLineDetection] = []
    for x1, y1, x2, y2 in segments[:, 0, :]:
        dx, dy = x2 - x1, y2 - y1
        length = float(np.hypot(dx, dy))
        if length <= 0:
            continue
        angle = abs(float(np.degrees(np.arctan2(dy, dx))))
        deviation = min(abs(angle - 90.0), abs(angle - 270.0))
        if deviation > angle_tolerance_deg:
            continue
        mask = np.zeros(gray.shape, dtype=np.uint8)
        cv2.line(mask, (int(x1), int(y1)), (int(x2), int(y2)), 255, 5)
        stroke_pixels = cv2.bitwise_and(edges, edges, mask=mask)
        ys, xs = np.where(stroke_pixels > 0)
        width_px = float(max(1.0, np.percentile(xs, 95) - np.percentile(xs, 5))) if xs.size > 0 else 1.0
        confidence = max(0.0, 1.0 - deviation / max(angle_tolerance_deg, 1e-6))
        detections.append(VerticalLineDetection((x1 + x2) / 2.0, float(min(y1, y2)), float(max(y1, y2)), length, width_px, angle, confidence))
    return sorted(detections, key=lambda d: (d.confidence, d.length_px), reverse=True)


def detection_to_dict(d: VerticalLineDetection) -> dict[str, Any]:
    return {
        "primitive": "line",
        "orientation": "vertical",
        "x_center": round(d.x_center, 2),
        "y_top": round(d.y_top, 2),
        "y_bottom": round(d.y_bottom, 2),
        "length_px": round(d.length_px, 2),
        "stroke_width_px": round(d.width_px, 2),
        "angle_deg": round(d.angle_deg, 2),
        "confidence": round(d.confidence, 4),
    }


def detect_primitive_colors(
    image,
    *,
    fill_mask=None,
    stroke_mask=None,
    trim_percent: float = 0.05,
) -> PrimitiveColorDetection:
    """Estimate robust fill/stroke colors from optional primitive masks."""
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError("detect_primitive_colors requires numpy and opencv-python") from exc

    if image.ndim == 2:
        bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    else:
        bgr = image
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    def _extract(mask) -> tuple[tuple[int, int, int] | None, str | None, float]:
        if mask is None:
            return None, None, 0.0
        pixels = rgb[mask > 0]
        if pixels.size == 0:
            return None, None, 0.0
        low_q = int(max(0, trim_percent * 100))
        high_q = int(min(100, 100 - trim_percent * 100))
        robust = np.percentile(pixels, [low_q, high_q], axis=0)
        keep = np.all((pixels >= robust[0]) & (pixels <= robust[1]), axis=1)
        kept = pixels[keep] if np.any(keep) else pixels
        mean_rgb = tuple(int(round(v)) for v in np.mean(kept, axis=0))
        confidence = float(max(0.0, 1.0 - (np.std(kept, axis=0).mean() / 128.0)))
        hex_color = f"#{mean_rgb[0]:02X}{mean_rgb[1]:02X}{mean_rgb[2]:02X}"
        return mean_rgb, hex_color, confidence

    fill_rgb, fill_hex, fill_confidence = _extract(fill_mask)
    stroke_rgb, stroke_hex, stroke_confidence = _extract(stroke_mask)
    return PrimitiveColorDetection(
        fill_rgb=fill_rgb,
        stroke_rgb=stroke_rgb,
        fill_hex=fill_hex,
        stroke_hex=stroke_hex,
        fill_confidence=round(fill_confidence, 4),
        stroke_confidence=round(stroke_confidence, 4),
    )


@dataclass(frozen=True)
class ShapeClassification:
    primitive: str
    confidence: float
    vertices: int
    is_convex: bool


def classify_contour_shape(contour, *, approx_epsilon_factor: float = 0.02) -> ShapeClassification:
    """Classify contour as triangle/rectangle/arrow/unknown via polygon and convexity heuristics."""
    try:
        import cv2  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError("classify_contour_shape requires opencv-python") from exc

    perimeter = float(cv2.arcLength(contour, True))
    if perimeter <= 0:
        return ShapeClassification("unknown", 0.0, 0, False)
    approx = cv2.approxPolyDP(contour, approx_epsilon_factor * perimeter, True)
    vertices = int(len(approx))
    is_convex = bool(cv2.isContourConvex(approx))

    if vertices == 3:
        return ShapeClassification("triangle", 0.95, vertices, True)
    if vertices == 4 and is_convex:
        return ShapeClassification("rectangle", 0.9, vertices, True)

    if not is_convex and vertices >= 5:
        hull = cv2.convexHull(approx)
        defects = max(0, int(len(hull) - len(approx)))
        confidence = min(0.92, 0.6 + defects * 0.08)
        return ShapeClassification("arrow", confidence, vertices, False)

    return ShapeClassification("unknown", 0.3 if vertices >= 3 else 0.0, vertices, is_convex)
