from __future__ import annotations

import argparse
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
        choices=["contract", "minus-roi", "circle-ring-seed"],
        default="contract",
    )
    args = parser.parse_args()
    if args.report == "minus-roi":
        summary = run_minus_roi_report(Path(args.output_dir))
    elif args.report == "circle-ring-seed":
        summary = run_circle_ring_seed_report(Path(args.output_dir))
    else:
        summary = run_contract_report(Path(args.output_dir))
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
