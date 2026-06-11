from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if __package__ in {None, ""}:
    sys.path.insert(0, str(PROJECT_ROOT))

if importlib.util.find_spec("numpy") is None:
    py_tag = f"py{sys.version_info.major}{sys.version_info.minor}"
    vendor_site_packages = PROJECT_ROOT / "vendor" / f"linux-{py_tag}" / "site-packages"
    if vendor_site_packages.exists() and str(vendor_site_packages) not in sys.path:
        sys.path.insert(0, str(vendor_site_packages))

from tools.shape_detection import (
    detect_circle_rings,
    detect_horizontal_rules,
    detect_primitive_colors,
    detect_vertical_lines,
)
from tools.shape_detection_eval import make_synthetic_image
from src.iCCModules import imageCompositeConverterGeometryIr as geometry_ir_helpers


@dataclass(frozen=True)
class PerceptionPrimitiveCandidate:
    """Stable v1 contract for primitive detections before Geometry-IR seeding."""

    schema_version: str
    kind: str
    bbox: dict[str, float]
    center: dict[str, float]
    geometry: dict[str, Any]
    color: dict[str, Any]
    confidence: float
    roi: dict[str, Any]
    evidence: dict[str, Any]
    source: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _round_number(value: float, digits: int = 3) -> float:
    return round(float(value), digits)


def _bbox_dict(x: float, y: float, width: float, height: float) -> dict[str, float]:
    return {
        "x": _round_number(x),
        "y": _round_number(y),
        "width": _round_number(width),
        "height": _round_number(height),
    }


def _center_dict(x: float, y: float) -> dict[str, float]:
    return {"x": _round_number(x), "y": _round_number(y)}


def _full_image_roi(image, *, hint: str = "full_image") -> dict[str, Any]:
    height, width = image.shape[:2]
    return {"type": "image", "hint": hint, "bbox": _bbox_dict(0, 0, width, height)}


def description_hint_to_roi(image, description: str | None) -> dict[str, Any]:
    """Derive a small ROI from German/English position hints in the description."""
    height, width = image.shape[:2]
    text = (description or "").casefold()
    x, y, w, h = 0.0, 0.0, float(width), float(height)
    hints: list[str] = []

    if any(token in text for token in ["oben", "top", "upper"]):
        y = 0.0
        h = height * 0.42
        hints.append("top")
    if any(token in text for token in ["unten", "bottom", "lower"]):
        y = height * 0.58
        h = height * 0.42
        hints.append("bottom")
    if any(
        token in text
        for token in ["mittig", "mitte", "symmetrieachse", "center", "zentral"]
    ):
        x = width * 0.2
        w = width * 0.6
        hints.append("center")
    elif "links" in text or "left" in text:
        x = 0.0
        w = width * 0.55
        hints.append("left")
    elif "rechts" in text or "right" in text:
        x = width * 0.45
        w = width * 0.55
        hints.append("right")

    return {
        "type": "description_hint",
        "hint": "+".join(hints) or "full_image",
        "bbox": _bbox_dict(x, y, w, h),
        "description": description or "",
    }


def _roi_tuple(roi: dict[str, Any]) -> tuple[int, int, int, int]:
    bbox = roi["bbox"]
    return (
        int(round(bbox["x"])),
        int(round(bbox["y"])),
        int(round(bbox["width"])),
        int(round(bbox["height"])),
    )


def _color_dict(color_detection) -> dict[str, Any]:
    return {
        "fill_rgb": color_detection.fill_rgb,
        "stroke_rgb": color_detection.stroke_rgb,
        "fill_hex": color_detection.fill_hex,
        "stroke_hex": color_detection.stroke_hex,
        "fill_confidence": color_detection.fill_confidence,
        "stroke_confidence": color_detection.stroke_confidence,
    }


def _normalized_bbox_dict(
    candidate: PerceptionPrimitiveCandidate, image
) -> list[float]:
    height, width = image.shape[:2]
    bbox = candidate.bbox
    return [
        _round_number(float(bbox["x"]) / max(float(width), 1.0), 5),
        _round_number(float(bbox["y"]) / max(float(height), 1.0), 5),
        _round_number(float(bbox["width"]) / max(float(width), 1.0), 5),
        _round_number(float(bbox["height"]) / max(float(height), 1.0), 5),
    ]


def make_circle_ring_candidate(
    image,
    detection,
    *,
    source: str = "circle_ring_detector",
) -> PerceptionPrimitiveCandidate:
    import cv2  # type: ignore
    import numpy as np  # type: ignore

    x, y, w, h = detection.bbox
    fill_mask = np.zeros(image.shape[:2], dtype=np.uint8)
    stroke_mask = np.zeros(image.shape[:2], dtype=np.uint8)
    cv2.circle(
        fill_mask,
        (int(round(detection.cx)), int(round(detection.cy))),
        int(round(detection.radius_px)),
        255,
        thickness=-1,
    )
    if detection.ring and detection.inner_radius_px > 0:
        cv2.circle(
            fill_mask,
            (int(round(detection.cx)), int(round(detection.cy))),
            int(round(detection.inner_radius_px)),
            0,
            thickness=-1,
        )
    cv2.circle(
        stroke_mask,
        (int(round(detection.cx)), int(round(detection.cy))),
        int(round(detection.radius_px)),
        255,
        thickness=max(1, int(round(detection.stroke_width_px))),
    )
    color = _color_dict(
        detect_primitive_colors(image, fill_mask=fill_mask, stroke_mask=stroke_mask)
    )
    kind = "ring" if detection.ring else "circle"
    height, width = image.shape[:2]
    normalized_bbox = [
        _round_number(x / max(float(width), 1.0), 5),
        _round_number(y / max(float(height), 1.0), 5),
        _round_number(w / max(float(width), 1.0), 5),
        _round_number(h / max(float(height), 1.0), 5),
    ]
    return PerceptionPrimitiveCandidate(
        schema_version="perception_primitive_candidate_v1",
        kind=kind,
        bbox=_bbox_dict(x, y, w, h),
        center=_center_dict(detection.cx, detection.cy),
        geometry={
            "radius_px": _round_number(detection.radius_px),
            "inner_radius_px": _round_number(detection.inner_radius_px),
            "stroke_width_px": _round_number(detection.stroke_width_px),
            "circularity": _round_number(detection.circularity, 4),
            "ring": bool(detection.ring),
            "fill_ratio": _round_number(detection.fill_ratio, 4),
            "geometry_ir_kind": "CircleBackground",
            "geometry_ir_bbox": normalized_bbox,
        },
        color=color,
        confidence=_round_number(detection.confidence, 4),
        roi=_full_image_roi(image),
        evidence={
            "detector": "detect_circle_rings",
            "detection_source": detection.detection_source,
            "threshold_model": "hough_plus_foreground_mask",
        },
        source=source,
    )


def detect_circle_ring_candidates(
    image,
    *,
    source: str = "circle_ring_detector",
) -> list[PerceptionPrimitiveCandidate]:
    """Return stabilized circle/ring candidates prepared for CircleBackground seeding."""
    return [
        make_circle_ring_candidate(image, detection, source=source)
        for detection in detect_circle_rings(image)
    ]


def merge_circle_ring_candidates_into_geometry_ir(
    image,
    candidates: list[PerceptionPrimitiveCandidate],
    geometry_ir: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    """Merge the strongest circle/ring perception candidate into a CircleBackground Geometry-IR element."""
    merged = [dict(element) for element in (geometry_ir or [])]
    circle_candidates = [
        candidate for candidate in candidates if candidate.kind in {"circle", "ring"}
    ]
    if not circle_candidates:
        return merged
    best = sorted(circle_candidates, key=lambda item: item.confidence, reverse=True)[0]
    bbox = best.geometry.get("geometry_ir_bbox")
    if not isinstance(bbox, list) or len(bbox) != 4:
        bbox = _normalized_bbox_dict(best, image)
    color = best.color
    seed = {
        "kind": "CircleBackground",
        "id": "perception_circle_background",
        "bbox": bbox,
        "fill": color.get("fill_hex") or ("none" if best.kind == "ring" else "#d8d8d8"),
        "stroke": color.get("stroke_hex") or "#666666",
        "stroke_width": _round_number(
            max(
                0.006,
                float(best.geometry.get("stroke_width_px", 1.0))
                / max(float(min(image.shape[:2])), 1.0),
            ),
            5,
        ),
        "perception_seed": {
            "kind": best.kind,
            "confidence": best.confidence,
            "source": best.source,
            "detector": best.evidence.get("detector"),
            "detection_source": best.evidence.get("detection_source"),
            "candidate_schema_version": best.schema_version,
        },
    }
    for idx, element in enumerate(merged):
        if element.get("kind") == "CircleBackground":
            updated = dict(element)
            updated.update(
                {
                    key: value
                    for key, value in seed.items()
                    if key not in {"id"} or not updated.get("id")
                }
            )
            updated["perception_seed"] = seed["perception_seed"]
            merged[idx] = updated
            return merged
    return [seed, *merged]


def build_circle_seeded_geometry_ir(
    image,
    *,
    description: str | None = None,
    source: str = "circle_ring_detector",
) -> list[dict[str, object]]:
    """Build description Geometry-IR and pre-seed CircleBackground from detected circles/rings."""
    base = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl(description or "")
    return merge_circle_ring_candidates_into_geometry_ir(
        image, detect_circle_ring_candidates(image, source=source), base
    )


def make_horizontal_rule_candidate(
    image,
    detection,
    *,
    roi: dict[str, Any] | None = None,
    source: str = "horizontal_rule_detector",
) -> PerceptionPrimitiveCandidate:
    import cv2  # type: ignore
    import numpy as np  # type: ignore

    x = detection.x_left
    y = detection.y_center - detection.height_px / 2.0
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    cv2.rectangle(
        mask,
        (int(round(detection.x_left)), int(round(y))),
        (int(round(detection.x_right)), int(round(y + detection.height_px))),
        255,
        thickness=-1,
    )
    color = _color_dict(detect_primitive_colors(image, stroke_mask=mask))
    return PerceptionPrimitiveCandidate(
        schema_version="perception_primitive_candidate_v1",
        kind="horizontal_rule",
        bbox=_bbox_dict(x, y, detection.length_px, detection.height_px),
        center=_center_dict(
            (detection.x_left + detection.x_right) / 2.0, detection.y_center
        ),
        geometry={
            "orientation": "horizontal",
            "x_left": _round_number(detection.x_left),
            "x_right": _round_number(detection.x_right),
            "y_center": _round_number(detection.y_center),
            "length_px": _round_number(detection.length_px),
            "stroke_width_px": _round_number(detection.height_px),
            "angle_deg": _round_number(detection.angle_deg),
            "text_equivalent": "-",
            "geometry_ir_kind": "HorizontalRule",
        },
        color=color,
        confidence=_round_number(detection.confidence, 4),
        roi=roi or _full_image_roi(image),
        evidence={
            "detector": "detect_horizontal_rules",
            "threshold_model": "dark_contour_horizontal_opening",
            "description_hint": (roi or {}).get("hint"),
        },
        source=source,
    )


def make_line_candidate(
    image, detection, *, source: str = "hough"
) -> PerceptionPrimitiveCandidate:
    x = detection.x_center - detection.width_px / 2.0
    y = detection.y_top
    height = detection.y_bottom - detection.y_top
    return PerceptionPrimitiveCandidate(
        schema_version="perception_primitive_candidate_v1",
        kind="line",
        bbox=_bbox_dict(x, y, detection.width_px, height),
        center=_center_dict(detection.x_center, detection.y_top + height / 2.0),
        geometry={
            "orientation": "vertical",
            "x_center": _round_number(detection.x_center),
            "y_top": _round_number(detection.y_top),
            "y_bottom": _round_number(detection.y_bottom),
            "length_px": _round_number(detection.length_px),
            "stroke_width_px": _round_number(detection.width_px),
            "angle_deg": _round_number(detection.angle_deg),
        },
        color={
            "fill_rgb": None,
            "stroke_rgb": None,
            "fill_hex": None,
            "stroke_hex": None,
            "fill_confidence": 0.0,
            "stroke_confidence": 0.0,
        },
        confidence=_round_number(detection.confidence, 4),
        roi=_full_image_roi(image),
        evidence={
            "detector": "detect_vertical_lines",
            "edge_model": "canny+hough_lines_p",
        },
        source=source,
    )


def _contour_candidates(image, *, source: str) -> list[PerceptionPrimitiveCandidate]:
    import cv2  # type: ignore
    import numpy as np  # type: ignore

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    _, threshold = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(
        threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    candidates: list[PerceptionPrimitiveCandidate] = []

    for contour in contours:
        area = float(cv2.contourArea(contour))
        if area < 25:
            continue
        perimeter = float(cv2.arcLength(contour, True))
        if perimeter <= 0:
            continue
        x, y, w, h = cv2.boundingRect(contour)
        circularity = float(4 * np.pi * area / (perimeter * perimeter + 1e-9))
        approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
        vertices = int(len(approx))
        fill_mask = np.zeros(gray.shape, dtype=np.uint8)
        cv2.drawContours(fill_mask, [contour], -1, 255, thickness=-1)
        stroke_mask = np.zeros(gray.shape, dtype=np.uint8)
        cv2.drawContours(stroke_mask, [contour], -1, 255, thickness=2)
        color = _color_dict(
            detect_primitive_colors(image, fill_mask=fill_mask, stroke_mask=stroke_mask)
        )

        if circularity > 0.82:
            (cx, cy), radius = cv2.minEnclosingCircle(contour)
            candidates.append(
                PerceptionPrimitiveCandidate(
                    schema_version="perception_primitive_candidate_v1",
                    kind="circle",
                    bbox=_bbox_dict(x, y, w, h),
                    center=_center_dict(cx, cy),
                    geometry={
                        "radius_px": _round_number(radius),
                        "area_px": _round_number(area),
                        "circularity": _round_number(circularity, 4),
                        "ring": False,
                    },
                    color=color,
                    confidence=_round_number(min(0.99, max(0.0, circularity)), 4),
                    roi=_full_image_roi(image),
                    evidence={
                        "detector": "contour",
                        "vertices": vertices,
                        "area_px": _round_number(area),
                    },
                    source=source,
                )
            )
            continue

        if vertices == 4 and bool(cv2.isContourConvex(approx)):
            rect = cv2.minAreaRect(contour)
            (_, _), (rw, rh), angle = rect
            extent = area / float(max(w * h, 1))
            candidates.append(
                PerceptionPrimitiveCandidate(
                    schema_version="perception_primitive_candidate_v1",
                    kind="rectangle",
                    bbox=_bbox_dict(x, y, w, h),
                    center=_center_dict(x + w / 2.0, y + h / 2.0),
                    geometry={
                        "width_px": _round_number(rw),
                        "height_px": _round_number(rh),
                        "angle_deg": _round_number(angle),
                        "area_px": _round_number(area),
                        "extent": _round_number(extent, 4),
                    },
                    color=color,
                    confidence=_round_number(
                        min(0.98, 0.7 + max(0.0, extent) * 0.25), 4
                    ),
                    roi=_full_image_roi(image),
                    evidence={
                        "detector": "contour",
                        "vertices": vertices,
                        "convex": True,
                    },
                    source=source,
                )
            )

    return sorted(candidates, key=lambda item: item.confidence, reverse=True)


def detect_minus_candidates(
    image,
    *,
    description: str | None = None,
    source: str = "description_roi_minus",
) -> list[PerceptionPrimitiveCandidate]:
    """Return horizontal-rule/minus candidates, constrained by description-derived ROI when available."""
    roi = description_hint_to_roi(image, description)
    detections = detect_horizontal_rules(image, roi_bbox=_roi_tuple(roi))
    return [
        make_horizontal_rule_candidate(image, detection, roi=roi, source=source)
        for detection in detections
    ]


def _glyph_tokens_from_description(description: str | None) -> list[str]:
    import re

    text = description or ""
    quoted = re.findall(r"[`\"']([^`\"']{1,6})[`\"']", text)
    tokens: list[str] = []
    for token in quoted:
        cleaned = token.strip()
        if cleaned:
            tokens.append(cleaned.upper())

    upper_text = text.upper()
    for token in ["M", "+", "-", "VOC", "CO2"]:
        if token in tokens:
            continue
        if token in {"+", "-"}:
            if token in text:
                tokens.append(token)
        elif re.search(rf"(?<![A-Z0-9]){re.escape(token)}(?![A-Z0-9])", upper_text):
            tokens.append(token)

    return tokens or ["M", "+", "-", "VOC", "CO2"]


def _threshold_text_image(image):
    import cv2  # type: ignore

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    _, threshold = cv2.threshold(gray, 210, 255, cv2.THRESH_BINARY_INV)
    return threshold


def _render_glyph_template(text: str, *, font_scale: float, thickness: int):
    import cv2  # type: ignore
    import numpy as np  # type: ignore

    font = cv2.FONT_HERSHEY_SIMPLEX
    (width, height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    canvas = np.full((height + baseline + 16, width + 16, 3), 255, dtype=np.uint8)
    cv2.putText(
        canvas,
        text,
        (8, 8 + height),
        font,
        font_scale,
        (0, 0, 0),
        thickness,
        cv2.LINE_AA,
    )
    threshold = _threshold_text_image(canvas)
    coords = cv2.findNonZero(threshold)
    if coords is None:
        return threshold
    x, y, w, h = cv2.boundingRect(coords)
    return threshold[y : y + h, x : x + w]


def _best_template_match(binary_roi, text: str) -> dict[str, Any] | None:
    import cv2  # type: ignore

    best: dict[str, Any] | None = None
    roi_height, roi_width = binary_roi.shape[:2]
    for scale in [0.65, 0.85, 1.05, 1.25, 1.5, 1.8, 2.1]:
        for thickness in [2, 3, 4]:
            template = _render_glyph_template(
                text, font_scale=scale, thickness=thickness
            )
            template_height, template_width = template.shape[:2]
            if template_height > roi_height or template_width > roi_width:
                continue
            result = cv2.matchTemplate(binary_roi, template, cv2.TM_CCOEFF_NORMED)
            _, score, _, location = cv2.minMaxLoc(result)
            if best is None or score > best["score"]:
                best = {
                    "score": float(score),
                    "x": float(location[0]),
                    "y": float(location[1]),
                    "width": float(template_width),
                    "height": float(template_height),
                    "font_scale": float(scale),
                    "thickness": int(thickness),
                }
    return best


def make_text_glyph_candidate(
    image,
    *,
    text: str,
    match: dict[str, Any],
    roi: dict[str, Any] | None = None,
    source: str = "template_glyph_detector",
) -> PerceptionPrimitiveCandidate:
    import cv2  # type: ignore
    import numpy as np  # type: ignore

    roi = roi or _full_image_roi(image)
    roi_x, roi_y, _, _ = _roi_tuple(roi)
    x = roi_x + float(match["x"])
    y = roi_y + float(match["y"])
    w = float(match["width"])
    h = float(match["height"])
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    cv2.rectangle(
        mask,
        (int(round(x)), int(round(y))),
        (int(round(x + w)), int(round(y + h))),
        255,
        thickness=-1,
    )
    color = _color_dict(detect_primitive_colors(image, stroke_mask=mask))
    return PerceptionPrimitiveCandidate(
        schema_version="perception_primitive_candidate_v1",
        kind="text_glyph",
        bbox=_bbox_dict(x, y, w, h),
        center=_center_dict(x + w / 2.0, y + h / 2.0),
        geometry={
            "text": text,
            "glyph": text,
            "template_score": _round_number(float(match["score"]), 4),
            "font_model": "cv2.FONT_HERSHEY_SIMPLEX",
            "font_scale": _round_number(float(match["font_scale"]), 3),
            "stroke_width_px": int(match["thickness"]),
            "geometry_ir_kind": "TextGlyph",
        },
        color=color,
        confidence=_round_number(max(0.0, min(0.99, float(match["score"]))), 4),
        roi=roi,
        evidence={
            "detector": "template_match_text_glyph",
            "threshold_model": "binary_inverse_threshold_210",
            "description_hint": roi.get("hint"),
            "dependency_policy": "uses_existing_cv2_only_no_required_ocr_dependency",
        },
        source=source,
    )


def detect_text_glyph_candidates(
    image,
    *,
    description: str | None = None,
    glyphs: list[str] | tuple[str, ...] | set[str] | None = None,
    source: str = "template_glyph_detector",
    min_score: float = 0.42,
) -> list[PerceptionPrimitiveCandidate]:
    """Evaluate simple template-based glyph detection without adding a required OCR dependency."""
    roi = description_hint_to_roi(image, description)
    roi_x, roi_y, roi_w, roi_h = _roi_tuple(roi)
    binary = _threshold_text_image(image)
    binary_roi = binary[roi_y : roi_y + roi_h, roi_x : roi_x + roi_w]
    requested_glyphs = (
        list(glyphs)
        if glyphs is not None
        else _glyph_tokens_from_description(description)
    )
    candidates: list[PerceptionPrimitiveCandidate] = []
    for raw_glyph in requested_glyphs:
        glyph = str(raw_glyph).strip().upper()
        if not glyph:
            continue
        match = _best_template_match(binary_roi, glyph)
        if match is None or float(match["score"]) < min_score:
            continue
        candidates.append(
            make_text_glyph_candidate(
                image, text=glyph, match=match, roi=roi, source=source
            )
        )
    return sorted(candidates, key=lambda item: item.confidence, reverse=True)


def detect_perception_candidates(
    image,
    *,
    source: str = "perception_contract",
    description: str | None = None,
) -> list[PerceptionPrimitiveCandidate]:
    """Return line/circle/rectangle/minus detections in the shared PF1/PF2 contract."""
    candidates = [
        make_line_candidate(image, line, source="hough")
        for line in detect_vertical_lines(image)
    ]
    candidates.extend(
        detect_minus_candidates(image, description=description, source=source)
    )
    candidates.extend(detect_circle_ring_candidates(image, source=source))
    contour_candidates = [
        candidate
        for candidate in _contour_candidates(image, source=source)
        if candidate.kind != "circle"
    ]
    candidates.extend(contour_candidates)
    return sorted(candidates, key=lambda item: item.confidence, reverse=True)


def _candidate_normalized_bbox(
    candidate: PerceptionPrimitiveCandidate, image
) -> list[float]:
    bbox = candidate.geometry.get("geometry_ir_bbox")
    if isinstance(bbox, list) and len(bbox) == 4:
        return [_round_number(float(value), 5) for value in bbox]
    return _normalized_bbox_dict(candidate, image)


def merge_perception_candidates_into_geometry_ir(
    image,
    candidates: list[PerceptionPrimitiveCandidate],
    geometry_ir: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    """Merge image-derived candidates into the description Geometry-IR before fallback fitting."""
    merged = merge_circle_ring_candidates_into_geometry_ir(
        image, candidates, geometry_ir
    )
    existing_kinds = {str(element.get("kind", "")) for element in merged}

    horizontal_rules = [
        candidate for candidate in candidates if candidate.kind == "horizontal_rule"
    ]
    if horizontal_rules:
        best = sorted(horizontal_rules, key=lambda item: item.confidence, reverse=True)[
            0
        ]
        seed_meta = {
            "kind": best.kind,
            "confidence": best.confidence,
            "source": best.source,
            "detector": best.evidence.get("detector"),
            "candidate_schema_version": best.schema_version,
            "text_equivalent": best.geometry.get("text_equivalent"),
        }
        existing_rule_index = next(
            (
                idx
                for idx, element in enumerate(merged)
                if element.get("kind") in {"HorizontalRule", "MinusGlyph"}
            ),
            None,
        )
        if existing_rule_index is not None:
            updated = dict(merged[existing_rule_index])
            updated["perception_seed"] = seed_meta
            merged[existing_rule_index] = updated
        else:
            bbox = _candidate_normalized_bbox(best, image)
            stroke_width_px = float(
                best.geometry.get(
                    "stroke_width_px", max(best.bbox.get("height", 1.0), 1.0)
                )
            )
            stroke_width = _round_number(
                stroke_width_px / max(float(min(image.shape[:2])), 1.0), 5
            )
            merged.append(
                {
                    "kind": "HorizontalRule",
                    "id": "perception_horizontal_rule",
                    "bbox": bbox,
                    "stroke": best.color.get("stroke_hex") or "#4f4f4f",
                    "stroke_width": max(0.006, stroke_width),
                    "perception_seed": seed_meta,
                }
            )
        existing_kinds.add("HorizontalRule")

    rectangles = [
        candidate for candidate in candidates if candidate.kind == "rectangle"
    ]
    if (
        rectangles
        and "RectBorder" not in existing_kinds
        and "HalfDoubleRectBorder" not in existing_kinds
    ):
        best = sorted(rectangles, key=lambda item: item.confidence, reverse=True)[0]
        bbox = _candidate_normalized_bbox(best, image)
        stroke_width_px = max(
            1.0,
            min(
                float(best.bbox.get("width", 1.0)),
                float(best.bbox.get("height", 1.0)),
            )
            * 0.06,
        )
        merged.insert(
            0,
            {
                "kind": "RectBorder",
                "id": "perception_rect_border",
                "bbox": bbox,
                "fill": best.color.get("fill_hex") or "none",
                "stroke": best.color.get("stroke_hex") or "#666666",
                "stroke_width": _round_number(
                    stroke_width_px / max(float(min(image.shape[:2])), 1.0), 5
                ),
                "perception_seed": {
                    "kind": best.kind,
                    "confidence": best.confidence,
                    "source": best.source,
                    "detector": best.evidence.get("detector"),
                    "candidate_schema_version": best.schema_version,
                },
            },
        )

    return merged


def build_perception_seeded_geometry_ir(
    image,
    *,
    description: str | None = None,
    source: str = "perception_seeded_geometry_ir",
) -> list[dict[str, object]]:
    """Build description IR and seed it with PF candidates before non-composite fitting."""
    base = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl(description or "")
    candidates = detect_perception_candidates(
        image, source=source, description=description
    )
    return merge_perception_candidates_into_geometry_ir(image, candidates, base)


def _candidate_decision_key(
    candidate: PerceptionPrimitiveCandidate,
) -> tuple[str, str, float]:
    return (
        candidate.kind,
        str(candidate.evidence.get("detector", "")),
        _round_number(candidate.confidence, 4),
    )


def _seed_decision_keys(
    seeded_ir: list[dict[str, object]],
) -> set[tuple[str, str, float]]:
    keys: set[tuple[str, str, float]] = set()
    for element in seeded_ir:
        if not isinstance(element, dict):
            continue
        seed = element.get("perception_seed")
        if not isinstance(seed, dict):
            continue
        keys.add(
            (
                str(seed.get("kind", "")),
                str(seed.get("detector", "")),
                _round_number(float(seed.get("confidence", 0.0)), 4),
            )
        )
    return keys


def _render_svg_for_telemetry(svg: str, width: int, height: int):
    try:
        import cv2  # type: ignore
        import fitz  # type: ignore
        import numpy as np  # type: ignore
    except ModuleNotFoundError:
        return None
    from src.iCCModules.imageCompositeConverterRendering import (
        render_svg_to_numpy_inprocess,
    )

    return render_svg_to_numpy_inprocess(
        svg,
        width,
        height,
        fitz_module=fitz,
        np_module=np,
        cv2_module=cv2,
    )


def _calculate_telemetry_error(target, rendered) -> float | None:
    if rendered is None:
        return None
    import numpy as np  # type: ignore

    target_arr = np.asarray(target, dtype=np.float32)
    rendered_arr = np.asarray(rendered, dtype=np.float32)
    if target_arr.shape != rendered_arr.shape:
        return None
    return _round_number(float(np.mean(np.abs(target_arr - rendered_arr))), 6)


def _geometry_ir_error_for_telemetry(
    image, geometry_ir: list[dict[str, object]]
) -> tuple[float | None, str]:
    height, width = image.shape[:2]
    if geometry_ir:
        svg = geometry_ir_helpers.renderGeometryIrToSvgImpl(width, height, geometry_ir)
    else:
        svg = (
            f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
            'xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="#ffffff"/></svg>'
        )
    rendered = _render_svg_for_telemetry(svg, width, height)
    if rendered is None:
        return None, "render_unavailable"
    error = _calculate_telemetry_error(image, rendered)
    return error, "rendered" if error is not None else "error_unavailable"


def build_perception_telemetry_record(
    image,
    *,
    sample_id: str,
    description: str | None = None,
    image_path: str | None = None,
    source: str = "pf6_perception_telemetry",
) -> dict[str, Any]:
    """Build a PF6 telemetry record with candidates, decisions, seeds and error deltas."""
    base_ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl(description or "")
    candidates = detect_perception_candidates(
        image,
        source=source,
        description=description,
    )
    seeded_ir = merge_perception_candidates_into_geometry_ir(image, candidates, base_ir)
    accepted_keys = _seed_decision_keys(seeded_ir)
    candidate_rows: list[dict[str, Any]] = []
    for rank, candidate in enumerate(candidates, start=1):
        accepted = _candidate_decision_key(candidate) in accepted_keys
        candidate_rows.append(
            {
                "rank": rank,
                "candidate": candidate.to_dict(),
                "decision": "accepted" if accepted else "rejected",
                "reason": (
                    "selected_for_geometry_ir_seed"
                    if accepted
                    else "not_selected_lower_confidence_or_no_seed_mapping"
                ),
            }
        )

    selected_seed_elements = [
        element
        for element in seeded_ir
        if isinstance(element, dict) and element.get("perception_seed")
    ]
    error_before, render_status_before = _geometry_ir_error_for_telemetry(
        image, base_ir
    )
    error_after, render_status_after = _geometry_ir_error_for_telemetry(
        image, seeded_ir
    )
    if error_before is not None and error_after is not None:
        error_delta = _round_number(error_before - error_after, 6)
    else:
        error_delta = None
    height, width = image.shape[:2]
    return {
        "schema_version": "perception_telemetry_record_v1",
        "candidate_schema_version": "perception_primitive_candidate_v1",
        "sample_id": sample_id,
        "image_path": image_path,
        "image_size": {"width": int(width), "height": int(height)},
        "description": description or "",
        "runtime_status": "non_composite_perception_seeded_geometry_ir",
        "candidate_count": len(candidates),
        "accepted_candidate_count": sum(
            1 for row in candidate_rows if row["decision"] == "accepted"
        ),
        "rejected_candidate_count": sum(
            1 for row in candidate_rows if row["decision"] == "rejected"
        ),
        "candidates": candidate_rows,
        "selected_geometry_ir_seed_count": len(selected_seed_elements),
        "selected_geometry_ir_seeds": selected_seed_elements,
        "geometry_ir_before_seed_kinds": [element.get("kind") for element in base_ir],
        "geometry_ir_after_seed_kinds": [element.get("kind") for element in seeded_ir],
        "error_before_seed": error_before,
        "error_after_seed": error_after,
        "error_delta_before_minus_after": error_delta,
        "render_status_before_seed": render_status_before,
        "render_status_after_seed": render_status_after,
    }


def write_perception_telemetry_report(
    records: list[dict[str, Any]], output_dir: Path
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": "perception_telemetry_report_v1",
        "candidate_schema_version": "perception_primitive_candidate_v1",
        "records": records,
        "summary": {
            "samples": len(records),
            "total_candidates": sum(
                int(record["candidate_count"]) for record in records
            ),
            "accepted_candidates": sum(
                int(record["accepted_candidate_count"]) for record in records
            ),
            "rejected_candidates": sum(
                int(record["rejected_candidate_count"]) for record in records
            ),
            "all_have_selected_seed": all(
                int(record["selected_geometry_ir_seed_count"]) > 0 for record in records
            ),
        },
    }
    json_path = output_dir / "perception_telemetry_report_v1.json"
    csv_path = output_dir / "perception_telemetry_candidates_v1.csv"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "sample_id",
                "candidate_rank",
                "candidate_kind",
                "confidence",
                "decision",
                "reason",
                "seed_count",
                "error_before_seed",
                "error_after_seed",
                "error_delta_before_minus_after",
            ],
        )
        writer.writeheader()
        for record in records:
            for row in record["candidates"]:
                candidate = row["candidate"]
                writer.writerow(
                    {
                        "sample_id": record["sample_id"],
                        "candidate_rank": row["rank"],
                        "candidate_kind": candidate["kind"],
                        "confidence": candidate["confidence"],
                        "decision": row["decision"],
                        "reason": row["reason"],
                        "seed_count": record["selected_geometry_ir_seed_count"],
                        "error_before_seed": record["error_before_seed"],
                        "error_after_seed": record["error_after_seed"],
                        "error_delta_before_minus_after": record[
                            "error_delta_before_minus_after"
                        ],
                    }
                )
    return {
        "samples": report["summary"]["samples"],
        "accepted_candidates": report["summary"]["accepted_candidates"],
        "json_report": str(json_path),
        "csv_report": str(csv_path),
        "all_have_selected_seed": report["summary"]["all_have_selected_seed"],
    }


def _perception_seed_family(kind: str) -> str:
    if kind in {"horizontal_rule", "line"}:
        return "minus_line"
    if kind in {"circle", "ring"}:
        return "circle_ring"
    if kind == "rectangle":
        return "rectangle"
    return kind


def _confidence_summary(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, "min": None, "max": None, "mean": None}
    rounded = [_round_number(value, 4) for value in values]
    return {
        "count": len(rounded),
        "min": min(rounded),
        "max": max(rounded),
        "mean": _round_number(sum(rounded) / len(rounded), 4),
    }


def _safe_divide(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return _round_number(numerator / denominator, 4)


def build_perception_seed_evaluation_record(
    image,
    *,
    sample_id: str,
    expected_family: str,
    expected_candidate_kinds: set[str],
    expected_seed_kinds: set[str],
    description: str | None = None,
    image_path: str | None = None,
    sample_type: str = "synthetic",
) -> dict[str, Any]:
    """Evaluate one PF5 sample from detection through Geometry-IR seed quality."""
    telemetry = build_perception_telemetry_record(
        image,
        sample_id=sample_id,
        image_path=image_path,
        description=description,
        source="pf5_perception_seed_evaluation",
    )
    candidates = telemetry["candidates"]
    predicted_kinds = [str(row["candidate"]["kind"]) for row in candidates]
    matching_candidates = [
        row
        for row in candidates
        if str(row["candidate"]["kind"]) in expected_candidate_kinds
    ]
    top_candidate_kind = predicted_kinds[0] if predicted_kinds else None
    top_candidate_family = (
        _perception_seed_family(top_candidate_kind) if top_candidate_kind else None
    )
    selected_seed_kinds = {
        str(seed.get("kind")) for seed in telemetry["selected_geometry_ir_seeds"]
    }
    detection_match = bool(matching_candidates)
    top_match = top_candidate_family == expected_family
    seed_match = bool(selected_seed_kinds & expected_seed_kinds)
    quality_delta = telemetry["error_delta_before_minus_after"]
    quality_improved = quality_delta is not None and float(quality_delta) > 0

    return {
        "sample_id": sample_id,
        "sample_type": sample_type,
        "image_path": image_path,
        "description": description or "",
        "expected_family": expected_family,
        "expected_candidate_kinds": sorted(expected_candidate_kinds),
        "expected_seed_kinds": sorted(expected_seed_kinds),
        "candidate_count": telemetry["candidate_count"],
        "predicted_candidate_kinds": predicted_kinds,
        "top_candidate_kind": top_candidate_kind,
        "top_candidate_family": top_candidate_family,
        "detection_match": detection_match,
        "top_candidate_match": top_match,
        "seed_match": seed_match,
        "matching_confidences": [
            row["candidate"]["confidence"] for row in matching_candidates
        ],
        "selected_geometry_ir_seed_kinds": sorted(selected_seed_kinds),
        "error_before_seed": telemetry["error_before_seed"],
        "error_after_seed": telemetry["error_after_seed"],
        "error_delta_before_minus_after": quality_delta,
        "quality_improved": quality_improved,
        "runtime_status": telemetry["runtime_status"],
    }


def summarize_perception_seed_evaluation(
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Summarize PF5 records as precision/recall, confidence and quality metrics."""
    families = sorted({str(record["expected_family"]) for record in records})
    by_family: dict[str, dict[str, Any]] = {}
    for family in families:
        family_records = [
            record for record in records if record["expected_family"] == family
        ]
        tp = sum(1 for record in family_records if record["top_candidate_match"])
        fn = sum(1 for record in family_records if not record["detection_match"])
        fp = sum(
            1
            for record in records
            if record.get("top_candidate_family") == family
            and record["expected_family"] != family
        )
        detection_tp = sum(1 for record in family_records if record["detection_match"])
        seed_tp = sum(1 for record in family_records if record["seed_match"])
        confidences = [
            float(confidence)
            for record in family_records
            for confidence in record["matching_confidences"]
        ]
        quality_deltas = [
            float(record["error_delta_before_minus_after"])
            for record in family_records
            if record["error_delta_before_minus_after"] is not None
        ]
        by_family[family] = {
            "samples": len(family_records),
            "true_positive_top_candidate": tp,
            "false_positive_top_candidate": fp,
            "false_negative_detection": fn,
            "top_candidate_precision": _safe_divide(tp, tp + fp),
            "detection_recall": _safe_divide(detection_tp, len(family_records)),
            "seed_recall": _safe_divide(seed_tp, len(family_records)),
            "confidence": _confidence_summary(confidences),
            "quality_delta_mean": (
                _round_number(sum(quality_deltas) / len(quality_deltas), 6)
                if quality_deltas
                else None
            ),
            "quality_improved_samples": sum(
                1 for record in family_records if record["quality_improved"]
            ),
        }

    total_tp = sum(
        int(metrics["true_positive_top_candidate"]) for metrics in by_family.values()
    )
    total_fp = sum(
        int(metrics["false_positive_top_candidate"]) for metrics in by_family.values()
    )
    detection_matches = sum(1 for record in records if record["detection_match"])
    seed_matches = sum(1 for record in records if record["seed_match"])
    return {
        "samples": len(records),
        "families": families,
        "by_family": by_family,
        "overall": {
            "top_candidate_precision": _safe_divide(total_tp, total_tp + total_fp),
            "detection_recall": _safe_divide(detection_matches, len(records)),
            "seed_recall": _safe_divide(seed_matches, len(records)),
            "all_detection_matched": detection_matches == len(records),
            "all_seed_matched": seed_matches == len(records),
            "quality_improved_samples": sum(
                1 for record in records if record["quality_improved"]
            ),
        },
    }


def write_perception_seed_evaluation_report(
    records: list[dict[str, Any]], output_dir: Path
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics = summarize_perception_seed_evaluation(records)
    report = {
        "schema_version": "perception_seed_evaluation_report_v1",
        "candidate_schema_version": "perception_primitive_candidate_v1",
        "records": records,
        "metrics": metrics,
        "open_real_image_cases": [
            {
                "family": "rectangle",
                "reason": "no stable real rectangle candidate is documented for PF5 yet",
            }
        ],
    }
    json_path = output_dir / "perception_seed_evaluation_report_v1.json"
    csv_path = output_dir / "perception_seed_evaluation_samples_v1.csv"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "sample_id",
                "sample_type",
                "expected_family",
                "top_candidate_family",
                "detection_match",
                "seed_match",
                "error_before_seed",
                "error_after_seed",
                "error_delta_before_minus_after",
                "quality_improved",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "sample_id": record["sample_id"],
                    "sample_type": record["sample_type"],
                    "expected_family": record["expected_family"],
                    "top_candidate_family": record["top_candidate_family"],
                    "detection_match": record["detection_match"],
                    "seed_match": record["seed_match"],
                    "error_before_seed": record["error_before_seed"],
                    "error_after_seed": record["error_after_seed"],
                    "error_delta_before_minus_after": record[
                        "error_delta_before_minus_after"
                    ],
                    "quality_improved": record["quality_improved"],
                }
            )
    return {
        "samples": metrics["samples"],
        "families": metrics["families"],
        "overall_top_candidate_precision": metrics["overall"][
            "top_candidate_precision"
        ],
        "overall_detection_recall": metrics["overall"]["detection_recall"],
        "overall_seed_recall": metrics["overall"]["seed_recall"],
        "json_report": str(json_path),
        "csv_report": str(csv_path),
    }


def _make_synthetic_glyph_image(text: str):
    import cv2  # type: ignore
    import numpy as np  # type: ignore

    image = np.full((180, 260, 3), 255, dtype=np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 2.0 if len(text) == 1 else 1.35
    thickness = 3
    (width, height), _ = cv2.getTextSize(text, font, scale, thickness)
    x = max(8, (image.shape[1] - width) // 2)
    y = max(height + 8, (image.shape[0] + height) // 2)
    cv2.putText(image, text, (x, y), font, scale, (0, 0, 0), thickness, cv2.LINE_AA)
    return image


def build_text_glyph_evaluation_record(
    image,
    *,
    sample_id: str,
    expected_text: str,
    description: str | None = None,
    image_path: str | None = None,
    sample_type: str = "synthetic",
) -> dict[str, Any]:
    """Evaluate PF7 template matching for one glyph/short-label sample."""
    candidates = detect_text_glyph_candidates(
        image,
        description=description,
        glyphs=[expected_text],
        source="pf7_text_glyph_evaluation",
    )
    top = candidates[0] if candidates else None
    top_text = str(top.geometry.get("text")) if top else None
    return {
        "sample_id": sample_id,
        "sample_type": sample_type,
        "image_path": image_path,
        "description": description or "",
        "expected_text": expected_text,
        "candidate_count": len(candidates),
        "top_text": top_text,
        "top_confidence": top.confidence if top else None,
        "match": top_text == expected_text.upper(),
        "top_candidate": top.to_dict() if top else None,
    }


def summarize_text_glyph_evaluation(records: list[dict[str, Any]]) -> dict[str, Any]:
    confidences = [
        float(record["top_confidence"])
        for record in records
        if record["top_confidence"] is not None
    ]
    matches = sum(1 for record in records if record["match"])
    return {
        "samples": len(records),
        "matched_samples": matches,
        "match_rate": _safe_divide(matches, len(records)),
        "all_matched": matches == len(records),
        "confidence": _confidence_summary(confidences),
    }


def write_text_glyph_evaluation_report(
    records: list[dict[str, Any]], output_dir: Path
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics = summarize_text_glyph_evaluation(records)
    report = {
        "schema_version": "perception_text_glyph_evaluation_report_v1",
        "candidate_schema_version": "perception_primitive_candidate_v1",
        "detector": "template_match_text_glyph",
        "dependency_policy": "no_new_required_dependency; uses existing cv2/numpy path",
        "scope": ["M", "+", "-", "short_label"],
        "records": records,
        "metrics": metrics,
        "follow_up": "PF8 should include this report's text/glyph signal as a Perception-Lerneffekt section in Plan-B rotations.",
    }
    json_path = output_dir / "perception_text_glyph_evaluation_report_v1.json"
    csv_path = output_dir / "perception_text_glyph_evaluation_samples_v1.csv"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "sample_id",
                "sample_type",
                "expected_text",
                "top_text",
                "candidate_count",
                "top_confidence",
                "match",
            ],
        )
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "sample_id": record["sample_id"],
                    "sample_type": record["sample_type"],
                    "expected_text": record["expected_text"],
                    "top_text": record["top_text"],
                    "candidate_count": record["candidate_count"],
                    "top_confidence": record["top_confidence"],
                    "match": record["match"],
                }
            )
    return {
        "samples": metrics["samples"],
        "matched_samples": metrics["matched_samples"],
        "match_rate": metrics["match_rate"],
        "all_matched": metrics["all_matched"],
        "json_report": str(json_path),
        "csv_report": str(csv_path),
    }


PLAN_B_PERCEPTION_TARGETS: list[dict[str, Any]] = [
    {
        "variant": "AC0733_1_L",
        "image_candidates": ["artifacts/images_to_convert/AC0733_1_L.jpg"],
        "plan_b_reason": "Kompaktes gedrehtes Symbol mit horizontal bleibendem P-Glyph und hoher Diff-Abweichung.",
        "perception_question": "Bleiben gedrehte Grundgeometrie und horizontaler P-Glyph als getrennte Primitive erkennbar?",
        "expected_first_primitive": "rotated_symbol_with_horizontal_p_glyph",
        "expected_candidate_kinds": {"rectangle", "line", "text_glyph"},
        "expected_seed_kinds": {"RectangleBackground", "TextGlyph"},
        "description": "Plan-B-Kandidat AC0733_1_L: gedrehte Grundgeometrie und horizontalen P-Glyph getrennt prüfen.",
    },
    {
        "variant": "AC0733_1_M",
        "image_candidates": ["artifacts/images_to_convert/AC0733_1_M.jpg"],
        "plan_b_reason": "Mittlere kompakte Variante des gedrehten Symbols mit horizontal bleibendem P-Glyph.",
        "perception_question": "Bleiben gedrehte Grundgeometrie und horizontaler P-Glyph auch in der mittleren Variante getrennt erkennbar?",
        "expected_first_primitive": "rotated_symbol_with_horizontal_p_glyph",
        "expected_candidate_kinds": {"rectangle", "line", "text_glyph"},
        "expected_seed_kinds": {"RectangleBackground", "TextGlyph"},
        "description": "Plan-B-Kandidat AC0733_1_M: gedrehte Grundgeometrie und horizontalen P-Glyph getrennt prüfen.",
    },
    {
        "variant": "AC0722_1_L",
        "image_candidates": ["artifacts/images_to_convert/AC0722_1_L.jpg"],
        "plan_b_reason": "Kompaktes links gedrehtes Kellen-Symbol mit rotem Quadrat und T-Glyph.",
        "perception_question": "Können horizontaler Anschluss, Quadratgrundkörper und T-Glyph als getrennte Primitive erkannt werden?",
        "expected_first_primitive": "left_connector_square_with_t_glyph",
        "expected_candidate_kinds": {"rectangle", "line", "text_glyph"},
        "expected_seed_kinds": {"RectangleBackground", "TextGlyph"},
        "description": "Plan-B-Kandidat AC0722_1_L: Anschluss, Quadratgrundkörper und T-Glyph getrennt prüfen.",
    },
    {
        "variant": "AC0723_1_S",
        "image_candidates": ["artifacts/images_to_convert/AC0723_1_S.jpg"],
        "plan_b_reason": "Kompakte vertikal gespiegelte Kellen-Variante mit quadratischem Grundkörper.",
        "perception_question": "Können vertikaler Anschluss und Quadratgrundkörper als getrennte Primitive erkannt werden?",
        "expected_first_primitive": "vertical_connector_with_square",
        "expected_candidate_kinds": {"rectangle", "line"},
        "expected_seed_kinds": {"RectangleBackground"},
        "description": "Plan-B-Kandidat AC0723_1_S: vertikalen Anschluss und Quadratgrundkörper getrennt prüfen.",
    },
    {
        "variant": "AC0732_1_M",
        "image_candidates": ["artifacts/images_to_convert/AC0732_1_M.jpg"],
        "plan_b_reason": "Mittlere kompakte Variante eines nach rechts gedrehten Symbols mit horizontal bleibendem P-Glyph.",
        "perception_question": "Bleiben nach rechts gedrehte Grundgeometrie und horizontaler P-Glyph als getrennte Primitive erkennbar?",
        "expected_first_primitive": "right_rotated_symbol_with_horizontal_p_glyph",
        "expected_candidate_kinds": {"rectangle", "line", "text_glyph"},
        "expected_seed_kinds": {"RectangleBackground", "TextGlyph"},
        "description": "Plan-B-Kandidat AC0732_1_M: nach rechts gedrehte Grundgeometrie und horizontalen P-Glyph getrennt prüfen.",
    },
]


def _resolve_first_existing_path(candidates: list[str]) -> Path | None:
    for candidate in candidates:
        path = PROJECT_ROOT / candidate
        if path.exists():
            return path
    return None


def _candidate_seed_kind(candidate: PerceptionPrimitiveCandidate) -> str | None:
    geometry_kind = candidate.geometry.get("geometry_ir_kind")
    return str(geometry_kind) if geometry_kind else None


def _plan_b_decision(
    *,
    matched_candidates: list[PerceptionPrimitiveCandidate],
    matched_seed_kinds: set[str],
    expected_seed_kinds: set[str],
) -> str:
    if not matched_candidates:
        return "noch nicht erkannt"
    if matched_seed_kinds & expected_seed_kinds:
        return "generalisiert"
    return "nur Sonderfall"


def build_plan_b_perception_linkage_record(target: dict[str, Any]) -> dict[str, Any]:
    """Build one PF8 Plan-B record with an explicit Perception-Lerneffekt decision."""
    image_path = _resolve_first_existing_path(list(target.get("image_candidates", [])))
    expected_candidate_kinds = {
        str(kind) for kind in target["expected_candidate_kinds"]
    }
    expected_seed_kinds = {str(kind) for kind in target["expected_seed_kinds"]}
    candidates: list[PerceptionPrimitiveCandidate] = []
    status = "image_not_available"
    if image_path is not None and importlib.util.find_spec("cv2") is not None:
        import cv2  # type: ignore

        image = cv2.imread(str(image_path))
        if image is not None:
            status = "evaluated"
            candidates = detect_perception_candidates(
                image,
                source="pf8_plan_b_perception_linkage",
                description=str(target.get("description", "")),
            )
            glyphs = target.get("glyphs")
            if glyphs:
                candidates.extend(
                    detect_text_glyph_candidates(
                        image,
                        description=str(target.get("description", "")),
                        glyphs=list(glyphs),
                        source="pf8_plan_b_text_glyph_linkage",
                    )
                )
                candidates = sorted(
                    candidates, key=lambda item: item.confidence, reverse=True
                )
        else:
            status = "image_read_failed"
    elif image_path is not None:
        status = "cv2_not_available"

    matched_candidates = [
        candidate
        for candidate in candidates
        if candidate.kind in expected_candidate_kinds
    ]
    matched_seed_kinds = {
        seed_kind
        for candidate in matched_candidates
        if (seed_kind := _candidate_seed_kind(candidate)) is not None
    }
    decision = _plan_b_decision(
        matched_candidates=matched_candidates,
        matched_seed_kinds=matched_seed_kinds,
        expected_seed_kinds=expected_seed_kinds,
    )
    top = (
        matched_candidates[0]
        if matched_candidates
        else (candidates[0] if candidates else None)
    )
    if decision == "generalisiert":
        next_action = "Im nächsten Plan-B-Paket als vorinitialisierten Geometry-IR-Seed protokollieren."
    elif decision == "nur Sonderfall":
        next_action = "Als Perception-Hinweis dokumentieren, aber noch keinen generischen Seed erzwingen."
    else:
        next_action = "Vor der Plan-B-Umsetzung zusätzliche Detector-/ROI-Regel oder manuelle Seed-Annahme festhalten."

    return {
        "schema_version": "plan_b_perception_linkage_record_v1",
        "variant": target["variant"],
        "image_path": str(image_path.relative_to(PROJECT_ROOT)) if image_path else None,
        "status": status,
        "plan_b_reason": target["plan_b_reason"],
        "description": target.get("description", ""),
        "perception_lerneffekt": {
            "question": target["perception_question"],
            "expected_first_primitive": target["expected_first_primitive"],
            "expected_candidate_kinds": sorted(expected_candidate_kinds),
            "expected_seed_kinds": sorted(expected_seed_kinds),
            "decision": decision,
            "matched_candidate_kinds": sorted(
                {candidate.kind for candidate in matched_candidates}
            ),
            "matched_seed_kinds": sorted(matched_seed_kinds),
            "top_candidate_kind": top.kind if top else None,
            "top_confidence": top.confidence if top else None,
            "next_action": next_action,
        },
        "candidate_count": len(candidates),
        "top_candidate": top.to_dict() if top else None,
    }


def summarize_plan_b_perception_linkage(
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    decisions = [record["perception_lerneffekt"]["decision"] for record in records]
    return {
        "samples": len(records),
        "evaluated_samples": sum(
            1 for record in records if record["status"] == "evaluated"
        ),
        "generalisiert": decisions.count("generalisiert"),
        "nur_sonderfall": decisions.count("nur Sonderfall"),
        "noch_nicht_erkannt": decisions.count("noch nicht erkannt"),
        "all_have_perception_lerneffekt": all(
            bool(record.get("perception_lerneffekt", {}).get("question"))
            and record.get("perception_lerneffekt", {}).get("decision")
            in {"generalisiert", "nur Sonderfall", "noch nicht erkannt"}
            for record in records
        ),
    }


def write_plan_b_perception_linkage_report(
    records: list[dict[str, Any]], output_dir: Path
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics = summarize_plan_b_perception_linkage(records)
    report = {
        "schema_version": "plan_b_perception_linkage_report_v1",
        "candidate_schema_version": "perception_primitive_candidate_v1",
        "plan_b_source": "PLAN_B_KANDIDATEN.md",
        "acceptance_rule": "Each upcoming Plan-B package carries exactly one Perception-Lerneffekt decision.",
        "allowed_decisions": ["generalisiert", "nur Sonderfall", "noch nicht erkannt"],
        "records": records,
        "metrics": metrics,
    }
    json_path = output_dir / "plan_b_perception_linkage_report_v1.json"
    csv_path = output_dir / "plan_b_perception_linkage_samples_v1.csv"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "variant",
                "image_path",
                "status",
                "expected_first_primitive",
                "decision",
                "matched_candidate_kinds",
                "matched_seed_kinds",
                "top_candidate_kind",
                "top_confidence",
                "next_action",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for record in records:
            lerneffekt = record["perception_lerneffekt"]
            writer.writerow(
                {
                    "variant": record["variant"],
                    "image_path": record["image_path"],
                    "status": record["status"],
                    "expected_first_primitive": lerneffekt["expected_first_primitive"],
                    "decision": lerneffekt["decision"],
                    "matched_candidate_kinds": ",".join(
                        lerneffekt["matched_candidate_kinds"]
                    ),
                    "matched_seed_kinds": ",".join(lerneffekt["matched_seed_kinds"]),
                    "top_candidate_kind": lerneffekt["top_candidate_kind"],
                    "top_confidence": lerneffekt["top_confidence"],
                    "next_action": lerneffekt["next_action"],
                }
            )
    return {
        "samples": metrics["samples"],
        "evaluated_samples": metrics["evaluated_samples"],
        "all_have_perception_lerneffekt": metrics["all_have_perception_lerneffekt"],
        "json_report": str(json_path),
        "csv_report": str(csv_path),
    }


def run_plan_b_perception_linkage_report(output_dir: Path) -> dict[str, Any]:
    """Run PF8 linkage between active Plan-B candidates and Perception-Lerneffekt decisions."""
    records = [
        build_plan_b_perception_linkage_record(target)
        for target in PLAN_B_PERCEPTION_TARGETS
    ]
    return write_plan_b_perception_linkage_report(records, output_dir)


def run_text_glyph_evaluation_report(output_dir: Path) -> dict[str, Any]:
    """Run PF7 glyph/short-label evaluation without introducing OCR as a hard dependency."""
    samples = [
        {
            "sample_id": "glyph_m_synthetic",
            "image": _make_synthetic_glyph_image("M"),
            "expected_text": "M",
            "description": "mittig steht der Buchstabe `M`",
        },
        {
            "sample_id": "glyph_plus_synthetic",
            "image": _make_synthetic_glyph_image("+"),
            "expected_text": "+",
            "description": "mittig steht ein `+`-Zeichen",
        },
        {
            "sample_id": "glyph_minus_synthetic",
            "image": _make_synthetic_glyph_image("-"),
            "expected_text": "-",
            "description": "mittig steht ein `-`-Zeichen",
        },
        {
            "sample_id": "short_label_voc_synthetic",
            "image": _make_synthetic_glyph_image("VOC"),
            "expected_text": "VOC",
            "description": "mittig steht das kurze Label `VOC`",
        },
    ]
    real_path = PROJECT_ROOT / "artifacts" / "images_to_convert" / "AC0120_L.jpg"
    try:
        import cv2  # type: ignore
    except ModuleNotFoundError:
        cv2 = None
    if cv2 is not None:
        real_image = cv2.imread(str(real_path))
        if real_image is not None:
            samples.append(
                {
                    "sample_id": "AC0120_L_plus_real",
                    "image": real_image,
                    "expected_text": "+",
                    "description": "oben mittig steht ein `+`-Zeichen",
                    "sample_type": "real",
                    "image_path": str(real_path.relative_to(PROJECT_ROOT)),
                }
            )

    records = [
        build_text_glyph_evaluation_record(
            sample["image"],
            sample_id=sample["sample_id"],
            expected_text=sample["expected_text"],
            description=sample["description"],
            image_path=sample.get("image_path"),
            sample_type=sample.get("sample_type", "synthetic"),
        )
        for sample in samples
    ]
    return write_text_glyph_evaluation_report(records, output_dir)


def run_perception_seed_evaluation_report(output_dir: Path) -> dict[str, Any]:
    """Build PF5 evaluation metrics for minus/line, circle/ring and rectangle seeds."""
    samples: list[dict[str, Any]] = [
        {
            "sample_id": "minus_line_synthetic",
            "image": make_synthetic_image("minus", "synthetic"),
            "description": "oben mittig befindet sich eine Markierung",
            "expected_family": "minus_line",
            "expected_candidate_kinds": {"horizontal_rule"},
            "expected_seed_kinds": {"HorizontalRule", "MinusGlyph"},
            "sample_type": "synthetic",
        },
        {
            "sample_id": "circle_ring_synthetic",
            "image": make_synthetic_image("circle", "synthetic"),
            "description": "Kompressor grau nach rechts",
            "expected_family": "circle_ring",
            "expected_candidate_kinds": {"circle", "ring"},
            "expected_seed_kinds": {"CircleBackground"},
            "sample_type": "synthetic",
        },
        {
            "sample_id": "rectangle_synthetic",
            "image": make_synthetic_image("rectangle", "synthetic"),
            "description": "",
            "expected_family": "rectangle",
            "expected_candidate_kinds": {"rectangle"},
            "expected_seed_kinds": {"RectBorder", "HalfDoubleRectBorder"},
            "sample_type": "synthetic",
        },
    ]

    real_path = PROJECT_ROOT / "artifacts" / "images_to_convert" / "AC0120_L.jpg"
    cv2_spec = importlib.util.find_spec("cv2")
    if cv2_spec is not None and real_path.exists():
        import cv2  # type: ignore

        real_image = cv2.imread(str(real_path))
        if real_image is not None:
            samples.append(
                {
                    "sample_id": "AC0120_L_minus_line_real",
                    "image": real_image,
                    "image_path": str(real_path.relative_to(PROJECT_ROOT)),
                    "description": (
                        'oben auf der vertikalen Symmetrieachse werden ein "+"- '
                        'und ein "-"-Zeichen eingefügt'
                    ),
                    "expected_family": "minus_line",
                    "expected_candidate_kinds": {"horizontal_rule"},
                    "expected_seed_kinds": {"HorizontalRule", "MinusGlyph"},
                    "sample_type": "real",
                }
            )

    records = [
        build_perception_seed_evaluation_record(
            sample["image"],
            sample_id=sample["sample_id"],
            image_path=sample.get("image_path"),
            description=sample.get("description"),
            expected_family=sample["expected_family"],
            expected_candidate_kinds=set(sample["expected_candidate_kinds"]),
            expected_seed_kinds=set(sample["expected_seed_kinds"]),
            sample_type=sample.get("sample_type", "synthetic"),
        )
        for sample in samples
    ]
    return write_perception_seed_evaluation_report(records, output_dir)


def run_perception_telemetry_report(output_dir: Path) -> dict[str, Any]:
    """Write PF6 JSON/CSV telemetry for a Plan-B-style single candidate run."""
    real_path = PROJECT_ROOT / "artifacts" / "images_to_convert" / "AC0120_L.jpg"
    description = 'Plan-B-Kandidat AC0120_L: oben auf der vertikalen Symmetrieachse werden ein "+"- und ein "-"-Zeichen eingefügt.'
    try:
        import cv2  # type: ignore
    except ModuleNotFoundError:
        cv2 = None
    if cv2 is not None and real_path.exists():
        image = cv2.imread(str(real_path))
        sample_id = "AC0120_L_plan_b_real"
        image_path = str(real_path.relative_to(PROJECT_ROOT))
    else:
        image = None
    if image is None:
        image = make_synthetic_image("minus", "synthetic")
        sample_id = "minus_top_center_plan_b_synthetic"
        image_path = None
    record = build_perception_telemetry_record(
        image,
        sample_id=sample_id,
        image_path=image_path,
        description=description,
        source="pf6_perception_telemetry",
    )
    return write_perception_telemetry_report([record], output_dir)


def run_minus_roi_report(output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    synthetic_description = 'oben mittig ist ein "-"-Zeichen'
    real_description = 'Wie AC0120-Bildbeschreibung; oben auf der vertikalen Symmetrieachse werden ein "+"- und ein "-"-Zeichen eingefügt.'
    samples: list[dict[str, Any]] = [
        {
            "sample_id": "minus_top_center_synthetic",
            "image": make_synthetic_image("minus", "synthetic"),
            "description": synthetic_description,
            "expected_kind": "horizontal_rule",
        },
    ]
    real_path = PROJECT_ROOT / "artifacts" / "images_to_convert" / "AC0120_L.jpg"
    try:
        import cv2  # type: ignore

        real_image = cv2.imread(str(real_path))
    except ModuleNotFoundError:
        real_image = None
    if real_image is not None:
        samples.append(
            {
                "sample_id": "AC0120_L_real",
                "image": real_image,
                "description": real_description,
                "expected_kind": "horizontal_rule",
                "image_path": str(real_path.relative_to(PROJECT_ROOT)),
            }
        )

    rows = []
    for sample in samples:
        candidates = detect_minus_candidates(
            sample["image"], description=sample["description"], source="pf2_minus_roi"
        )
        rows.append(
            {
                "sample_id": sample["sample_id"],
                "image_path": sample.get("image_path"),
                "description": sample["description"],
                "expected_kind": sample["expected_kind"],
                "candidate_count": len(candidates),
                "match": any(
                    candidate.kind == sample["expected_kind"]
                    for candidate in candidates
                ),
                "top_candidate": candidates[0].to_dict() if candidates else None,
            }
        )

    report = {
        "schema_version": "perception_minus_roi_report_v1",
        "candidate_schema_version": "perception_primitive_candidate_v1",
        "samples": rows,
        "accepted_kinds": ["horizontal_rule"],
    }
    report_path = output_dir / "perception_minus_roi_report_v1.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return {
        "samples": len(rows),
        "all_matched": all(row["match"] for row in rows),
        "json_report": str(report_path),
    }


def run_circle_ring_seed_report(output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    samples: list[dict[str, Any]] = [
        {
            "sample_id": "circle_synthetic",
            "image": make_synthetic_image("circle", "synthetic"),
            "description": "Kompressor nach rechts mit kreisförmigem Hintergrund",
            "expected_kind": "circle",
        },
        {
            "sample_id": "ring_synthetic",
            "image": make_synthetic_image("ring", "synthetic"),
            "description": "Plain-Ring Kreis Hintergrund",
            "expected_kind": "ring",
        },
    ]
    real_samples = [
        (
            "AC0201_S_real",
            PROJECT_ROOT / "artifacts" / "images_to_convert" / "AC0201_S.jpg",
            "AC0201 Kompressor-/Ventilkandidat mit Kreis",
            "circle",
        ),
        (
            "AC0800_S_real",
            PROJECT_ROOT / "artifacts" / "images_to_convert" / "AC0800_S.jpg",
            "AC0800 Plain-Ring Kreis",
            "circle",
        ),
    ]
    try:
        import cv2  # type: ignore
    except ModuleNotFoundError:
        cv2 = None
    if cv2 is not None:
        for sample_id, real_path, description, expected_kind in real_samples:
            real_image = cv2.imread(str(real_path))
            if real_image is None:
                continue
            samples.append(
                {
                    "sample_id": sample_id,
                    "image": real_image,
                    "description": description,
                    "expected_kind": expected_kind,
                    "image_path": str(real_path.relative_to(PROJECT_ROOT)),
                }
            )

    rows = []
    for sample in samples:
        candidates = detect_circle_ring_candidates(
            sample["image"], source="pf3_circle_ring_seed"
        )
        seeded_ir = merge_circle_ring_candidates_into_geometry_ir(
            sample["image"],
            candidates,
            geometry_ir_helpers.buildGeometryIrFromDescriptionImpl(
                sample["description"]
            ),
        )
        top_candidate = candidates[0] if candidates else None
        rows.append(
            {
                "sample_id": sample["sample_id"],
                "image_path": sample.get("image_path"),
                "description": sample["description"],
                "expected_kind": sample["expected_kind"],
                "candidate_count": len(candidates),
                "match": any(
                    candidate.kind == sample["expected_kind"]
                    for candidate in candidates
                ),
                "top_candidate": top_candidate.to_dict() if top_candidate else None,
                "geometry_ir_kinds": [element.get("kind") for element in seeded_ir],
                "circle_background": next(
                    (
                        element
                        for element in seeded_ir
                        if element.get("kind") == "CircleBackground"
                    ),
                    None,
                ),
            }
        )

    report = {
        "schema_version": "perception_circle_ring_seed_report_v1",
        "candidate_schema_version": "perception_primitive_candidate_v1",
        "samples": rows,
        "accepted_kinds": ["circle", "ring"],
        "geometry_ir_seed_kind": "CircleBackground",
    }
    report_path = output_dir / "perception_circle_ring_seed_report_v1.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return {
        "samples": len(rows),
        "all_matched": all(row["match"] for row in rows),
        "json_report": str(report_path),
    }


def run_perception_seeded_geometry_ir_report(output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    samples: list[dict[str, Any]] = [
        {
            "sample_id": "minus_seed_synthetic",
            "image": make_synthetic_image("minus", "synthetic"),
            "description": "oben mittig befindet sich eine Markierung",
            "expected_seed_kind": "HorizontalRule",
        },
        {
            "sample_id": "circle_seed_synthetic",
            "image": make_synthetic_image("circle", "synthetic"),
            "description": "Kompressor grau nach rechts",
            "expected_seed_kind": "CircleBackground",
        },
    ]

    rows = []
    for sample in samples:
        seeded_ir = build_perception_seeded_geometry_ir(
            sample["image"],
            description=sample["description"],
            source="pf4_perception_seeded_geometry_ir",
        )
        seeded_elements = [
            element
            for element in seeded_ir
            if isinstance(element, dict) and element.get("perception_seed")
        ]
        rows.append(
            {
                "sample_id": sample["sample_id"],
                "description": sample["description"],
                "expected_seed_kind": sample["expected_seed_kind"],
                "geometry_ir_kinds": [element.get("kind") for element in seeded_ir],
                "seeded_element_count": len(seeded_elements),
                "match": any(
                    element.get("kind") == sample["expected_seed_kind"]
                    and element.get("perception_seed")
                    for element in seeded_ir
                ),
                "seeded_elements": seeded_elements,
            }
        )

    report = {
        "schema_version": "perception_seeded_geometry_ir_report_v1",
        "candidate_schema_version": "perception_primitive_candidate_v1",
        "runtime_status": "non_composite_perception_seeded_geometry_ir",
        "samples": rows,
        "accepted_seed_kinds": ["CircleBackground", "HorizontalRule", "RectBorder"],
    }
    report_path = output_dir / "perception_seeded_geometry_ir_report_v1.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return {
        "samples": len(rows),
        "all_matched": all(row["match"] for row in rows),
        "json_report": str(report_path),
    }


def run_contract_report(output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    samples = ["line", "circle", "rectangle"]
    rows = []
    for sample in samples:
        image = make_synthetic_image(sample, "synthetic")
        candidates = detect_perception_candidates(image, source="synthetic_fixture")
        matching = [candidate for candidate in candidates if candidate.kind == sample]
        rows.append(
            {
                "sample_id": f"{sample}_synthetic",
                "expected_kind": sample,
                "candidate_count": len(candidates),
                "match": bool(matching),
                "top_candidate": (
                    (matching[0] if matching else candidates[0]).to_dict()
                    if candidates
                    else None
                ),
            }
        )

    report = {
        "schema_version": "perception_detection_contract_report_v1",
        "candidate_schema_version": "perception_primitive_candidate_v1",
        "samples": rows,
        "accepted_kinds": ["line", "circle", "rectangle"],
    }
    report_path = output_dir / "perception_detection_contract_v1_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return {
        "samples": len(rows),
        "all_matched": all(row["match"] for row in rows),
        "json_report": str(report_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir", default="artifacts/evaluation/perception_detection_contract_v1"
    )
    parser.add_argument(
        "--report",
        choices=[
            "contract",
            "minus-roi",
            "circle-ring-seed",
            "perception-seeded-ir",
            "perception-telemetry",
            "perception-seed-eval",
            "text-glyph-eval",
            "plan-b-perception-linkage",
        ],
        default="contract",
    )
    args = parser.parse_args()
    if args.report == "minus-roi":
        summary = run_minus_roi_report(Path(args.output_dir))
    elif args.report == "circle-ring-seed":
        summary = run_circle_ring_seed_report(Path(args.output_dir))
    elif args.report == "perception-seeded-ir":
        summary = run_perception_seeded_geometry_ir_report(Path(args.output_dir))
    elif args.report == "perception-telemetry":
        summary = run_perception_telemetry_report(Path(args.output_dir))
    elif args.report == "perception-seed-eval":
        summary = run_perception_seed_evaluation_report(Path(args.output_dir))
    elif args.report == "text-glyph-eval":
        summary = run_text_glyph_evaluation_report(Path(args.output_dir))
    elif args.report == "plan-b-perception-linkage":
        summary = run_plan_b_perception_linkage_report(Path(args.output_dir))
    else:
        summary = run_contract_report(Path(args.output_dir))
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
