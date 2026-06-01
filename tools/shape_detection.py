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
class HorizontalRuleDetection:
    x_left: float
    x_right: float
    y_center: float
    length_px: float
    height_px: float
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


@dataclass(frozen=True)
class CircleRingDetection:
    cx: float
    cy: float
    radius_px: float
    inner_radius_px: float
    bbox: tuple[float, float, float, float]
    circularity: float
    ring: bool
    fill_ratio: float
    stroke_width_px: float
    confidence: float
    detection_source: str


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
        raise RuntimeError(
            "detect_vertical_lines requires numpy and opencv-python"
        ) from exc

    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    edges = cv2.Canny(gray, canny_low, canny_high)
    segments = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 180,
        hough_threshold,
        minLineLength=min_length_px,
        maxLineGap=max_gap_px,
    )
    detections: list[VerticalLineDetection] = []
    if segments is not None:
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
            _, xs = np.where(stroke_pixels > 0)
            width_px = (
                float(max(1.0, np.percentile(xs, 95) - np.percentile(xs, 5)))
                if xs.size > 0
                else 1.0
            )
            confidence = max(0.0, 1.0 - deviation / max(angle_tolerance_deg, 1e-6))
            detections.append(
                VerticalLineDetection(
                    (x1 + x2) / 2.0,
                    float(min(y1, y2)),
                    float(max(y1, y2)),
                    length,
                    width_px,
                    angle,
                    confidence,
                )
            )

    height, width = gray.shape[:2]
    adaptive_min_length = float(min(min_length_px, max(5, round(height * 0.32))))
    threshold = cv2.threshold(gray, 215, 255, cv2.THRESH_BINARY_INV)[1]
    kernel_height = max(3, min(height, int(round(height * 0.36))))
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_height))
    opened = cv2.morphologyEx(threshold, cv2.MORPH_OPEN, kernel)
    contours, _ = cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if h < adaptive_min_length or w <= 0:
            continue
        aspect = h / max(float(w), 1.0)
        if aspect < 2.5:
            continue
        x_center = float(x + w / 2.0)
        y_top = float(y)
        y_bottom = float(y + h)
        duplicate = any(
            abs(existing.x_center - x_center) <= max(1.0, w)
            and abs(existing.y_top - y_top) <= 2.0
            and abs(existing.y_bottom - y_bottom) <= 2.0
            for existing in detections
        )
        if duplicate:
            continue
        fill_ratio = float(
            np.count_nonzero(opened[y : y + h, x : x + w]) / max(w * h, 1)
        )
        lower_half_bonus = 0.08 if y_top >= height * 0.45 else 0.0
        confidence = min(
            0.92,
            0.48
            + min(0.22, (aspect - 2.5) * 0.025)
            + min(0.16, (h / max(height, 1)) * 0.2)
            + min(0.08, fill_ratio * 0.08)
            + lower_half_bonus,
        )
        detections.append(
            VerticalLineDetection(
                x_center=x_center,
                y_top=y_top,
                y_bottom=y_bottom,
                length_px=float(h),
                width_px=float(max(1, w)),
                angle_deg=90.0,
                confidence=confidence,
            )
        )

    return sorted(detections, key=lambda d: (d.confidence, d.length_px), reverse=True)


def detect_horizontal_rules(
    image,
    *,
    roi_bbox: tuple[int, int, int, int] | None = None,
    threshold_value: int = 215,
    min_length_px: int | None = None,
    min_aspect_ratio: float = 2.0,
) -> list[HorizontalRuleDetection]:
    """Detect short horizontal rule/minus glyph candidates, optionally inside an ROI."""
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "detect_horizontal_rules requires numpy and opencv-python"
        ) from exc

    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    height, width = gray.shape[:2]
    if roi_bbox is None:
        x0, y0, rw, rh = 0, 0, width, height
    else:
        x, y, w, h = roi_bbox
        x0 = max(0, min(width - 1, int(round(x))))
        y0 = max(0, min(height - 1, int(round(y))))
        x1 = max(x0 + 1, min(width, int(round(x + w))))
        y1 = max(y0 + 1, min(height, int(round(y + h))))
        rw, rh = x1 - x0, y1 - y0

    roi = gray[y0 : y0 + rh, x0 : x0 + rw]
    if roi.size == 0:
        return []

    threshold = cv2.threshold(roi, threshold_value, 255, cv2.THRESH_BINARY_INV)[1]
    kernel_width = max(3, min(rw, int(round(rw * 0.12))))
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_width, 1))
    opened = cv2.morphologyEx(threshold, cv2.MORPH_OPEN, kernel)
    contours, _ = cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    minimum_length = float(
        min_length_px if min_length_px is not None else max(4, round(width * 0.08))
    )
    detections: list[HorizontalRuleDetection] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w < minimum_length or h <= 0:
            continue
        aspect = w / max(float(h), 1.0)
        if aspect < min_aspect_ratio:
            continue
        fill_ratio = float(
            np.count_nonzero(opened[y : y + h, x : x + w]) / max(w * h, 1)
        )
        rect = cv2.minAreaRect(contour)
        (_, _), (_, _), raw_angle = rect
        angle = float(raw_angle)
        if angle < -45.0:
            angle += 90.0
        angle_deviation = abs(angle)
        if angle_deviation > 15.0:
            continue
        confidence = min(
            0.99,
            max(
                0.0,
                0.45
                + min(0.35, (aspect - min_aspect_ratio) * 0.08)
                + min(0.15, fill_ratio * 0.15)
                + max(0.0, 0.04 - angle_deviation / 400.0),
            ),
        )
        detections.append(
            HorizontalRuleDetection(
                x_left=float(x0 + x),
                x_right=float(x0 + x + w),
                y_center=float(y0 + y + h / 2.0),
                length_px=float(w),
                height_px=float(h),
                angle_deg=angle,
                confidence=confidence,
            )
        )

    return sorted(detections, key=lambda d: (d.confidence, d.length_px), reverse=True)


def detect_circle_rings(
    image,
    *,
    threshold_value: int = 220,
    min_radius_px: int | None = None,
    max_radius_px: int | None = None,
) -> list[CircleRingDetection]:
    """Detect filled circles and ring/annulus candidates using Hough plus foreground-mask contours."""
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "detect_circle_rings requires numpy and opencv-python"
        ) from exc

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    height, width = gray.shape[:2]
    min_side = max(1, min(height, width))
    min_radius = int(
        min_radius_px if min_radius_px is not None else max(4, round(min_side * 0.08))
    )
    max_radius = int(
        max_radius_px
        if max_radius_px is not None
        else max(min_radius + 1, round(min_side * 0.48))
    )
    foreground = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY_INV)[1]

    def _ring_metrics(
        cx: float,
        cy: float,
        radius: float,
        contour_area: float,
        perimeter: float,
        bbox: tuple[float, float, float, float],
        source: str,
    ):
        yy, xx = np.ogrid[:height, :width]
        dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        outer = dist <= max(radius, 1.0)
        inner_probe = dist <= max(radius * 0.58, 1.0)
        ring_band_width = max(1.4, radius * 0.16)
        ring_band = np.abs(dist - radius) <= ring_band_width
        outer_fg = float(np.mean(foreground[outer] > 0)) if np.any(outer) else 0.0
        inner_fg = (
            float(np.mean(foreground[inner_probe] > 0)) if np.any(inner_probe) else 0.0
        )
        ring_fg = (
            float(np.mean(foreground[ring_band] > 0)) if np.any(ring_band) else 0.0
        )
        is_ring = ring_fg >= 0.22 and inner_fg < max(0.42, outer_fg * 0.65)
        inner_radius = radius * 0.58 if is_ring else 0.0
        circularity = (
            float(4.0 * np.pi * contour_area / (perimeter * perimeter + 1e-9))
            if perimeter > 0
            else 0.0
        )
        radius_score = min(1.0, max(0.0, radius / max(min_side * 0.18, 1.0)))
        shape_score = min(1.0, max(0.0, circularity))
        coverage_score = ring_fg if is_ring else outer_fg
        confidence = min(
            0.99,
            0.30 + 0.38 * shape_score + 0.22 * coverage_score + 0.09 * radius_score,
        )
        stroke_width = (
            max(1.0, radius - inner_radius) if is_ring else max(1.0, radius * 0.08)
        )
        return CircleRingDetection(
            cx=float(cx),
            cy=float(cy),
            radius_px=float(radius),
            inner_radius_px=float(inner_radius),
            bbox=tuple(float(v) for v in bbox),
            circularity=circularity,
            ring=bool(is_ring),
            fill_ratio=float(outer_fg),
            stroke_width_px=float(stroke_width),
            confidence=float(confidence),
            detection_source=source,
        )

    candidates: list[CircleRingDetection] = []
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.1,
        minDist=max(8.0, min_side * 0.25),
        param1=90,
        param2=max(8, int(round(min_side * 0.16))),
        minRadius=min_radius,
        maxRadius=max_radius,
    )
    if circles is not None and circles.size > 0:
        for cx, cy, radius in np.round(circles[0, :]).astype(int):
            r = float(max(min_radius, min(max_radius, int(radius))))
            x = max(0.0, float(cx) - r)
            y = max(0.0, float(cy) - r)
            bbox = (
                x,
                y,
                min(float(width) - x, 2.0 * r),
                min(float(height) - y, 2.0 * r),
            )
            contour_area = float(np.pi * r * r)
            perimeter = float(2.0 * np.pi * r)
            candidates.append(
                _ring_metrics(
                    float(cx), float(cy), r, contour_area, perimeter, bbox, "hough"
                )
            )

    contours, _ = cv2.findContours(
        foreground, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    for contour in contours:
        area = float(cv2.contourArea(contour))
        if area < max(30.0, float(min_radius * min_radius) * 0.35):
            continue
        perimeter = float(cv2.arcLength(contour, True))
        if perimeter <= 0:
            continue
        (cx, cy), radius = cv2.minEnclosingCircle(contour)
        if not (min_radius <= radius <= max_radius):
            continue
        x, y, w, h = cv2.boundingRect(contour)
        aspect = w / max(float(h), 1.0)
        if not 0.72 <= aspect <= 1.38:
            continue
        candidates.append(
            _ring_metrics(
                cx, cy, float(radius), area, perimeter, (x, y, w, h), "foreground_mask"
            )
        )

    deduped: list[CircleRingDetection] = []
    for candidate in sorted(candidates, key=lambda item: item.confidence, reverse=True):
        duplicate = False
        for kept in deduped:
            center_dist = float(
                np.hypot(candidate.cx - kept.cx, candidate.cy - kept.cy)
            )
            if center_dist <= max(3.0, kept.radius_px * 0.12) and abs(
                candidate.radius_px - kept.radius_px
            ) <= max(3.0, kept.radius_px * 0.16):
                duplicate = True
                break
        if not duplicate:
            deduped.append(candidate)
    return deduped


def detection_to_dict(
    d: VerticalLineDetection | HorizontalRuleDetection | CircleRingDetection,
) -> dict[str, Any]:
    if isinstance(d, CircleRingDetection):
        return {
            "primitive": "ring" if d.ring else "circle",
            "cx": round(d.cx, 2),
            "cy": round(d.cy, 2),
            "radius_px": round(d.radius_px, 2),
            "inner_radius_px": round(d.inner_radius_px, 2),
            "circularity": round(d.circularity, 4),
            "fill_ratio": round(d.fill_ratio, 4),
            "stroke_width_px": round(d.stroke_width_px, 2),
            "confidence": round(d.confidence, 4),
            "source": d.detection_source,
        }
    if isinstance(d, HorizontalRuleDetection):
        return {
            "primitive": "horizontal_rule",
            "orientation": "horizontal",
            "x_left": round(d.x_left, 2),
            "x_right": round(d.x_right, 2),
            "y_center": round(d.y_center, 2),
            "length_px": round(d.length_px, 2),
            "stroke_width_px": round(d.height_px, 2),
            "angle_deg": round(d.angle_deg, 2),
            "confidence": round(d.confidence, 4),
        }
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
        raise RuntimeError(
            "detect_primitive_colors requires numpy and opencv-python"
        ) from exc

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


def classify_contour_shape(
    contour, *, approx_epsilon_factor: float = 0.02
) -> ShapeClassification:
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

    return ShapeClassification(
        "unknown", 0.3 if vertices >= 3 else 0.0, vertices, is_convex
    )
