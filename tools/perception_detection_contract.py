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

from tools.shape_detection import detect_primitive_colors, detect_vertical_lines
from tools.shape_detection_eval import make_synthetic_image


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
    return {"x": _round_number(x), "y": _round_number(y), "width": _round_number(width), "height": _round_number(height)}


def _center_dict(x: float, y: float) -> dict[str, float]:
    return {"x": _round_number(x), "y": _round_number(y)}


def _full_image_roi(image, *, hint: str = "full_image") -> dict[str, Any]:
    height, width = image.shape[:2]
    return {"type": "image", "hint": hint, "bbox": _bbox_dict(0, 0, width, height)}


def _color_dict(color_detection) -> dict[str, Any]:
    return {
        "fill_rgb": color_detection.fill_rgb,
        "stroke_rgb": color_detection.stroke_rgb,
        "fill_hex": color_detection.fill_hex,
        "stroke_hex": color_detection.stroke_hex,
        "fill_confidence": color_detection.fill_confidence,
        "stroke_confidence": color_detection.stroke_confidence,
    }


def make_line_candidate(image, detection, *, source: str = "hough") -> PerceptionPrimitiveCandidate:
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
        evidence={"detector": "detect_vertical_lines", "edge_model": "canny+hough_lines_p"},
        source=source,
    )


def _contour_candidates(image, *, source: str) -> list[PerceptionPrimitiveCandidate]:
    import cv2  # type: ignore
    import numpy as np  # type: ignore

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    _, threshold = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
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
        color = _color_dict(detect_primitive_colors(image, fill_mask=fill_mask, stroke_mask=stroke_mask))

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
                    evidence={"detector": "contour", "vertices": vertices, "area_px": _round_number(area)},
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
                    confidence=_round_number(min(0.98, 0.7 + max(0.0, extent) * 0.25), 4),
                    roi=_full_image_roi(image),
                    evidence={"detector": "contour", "vertices": vertices, "convex": True},
                    source=source,
                )
            )

    return sorted(candidates, key=lambda item: item.confidence, reverse=True)


def detect_perception_candidates(image, *, source: str = "perception_contract") -> list[PerceptionPrimitiveCandidate]:
    """Return line/circle/rectangle detections in the shared PF1 contract."""
    candidates = [make_line_candidate(image, line, source="hough") for line in detect_vertical_lines(image)]
    candidates.extend(_contour_candidates(image, source=source))
    return sorted(candidates, key=lambda item: item.confidence, reverse=True)


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
                "top_candidate": (matching[0] if matching else candidates[0]).to_dict() if candidates else None,
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
    return {"samples": len(rows), "all_matched": all(row["match"] for row in rows), "json_report": str(report_path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="artifacts/evaluation/perception_detection_contract_v1")
    args = parser.parse_args()
    summary = run_contract_report(Path(args.output_dir))
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
