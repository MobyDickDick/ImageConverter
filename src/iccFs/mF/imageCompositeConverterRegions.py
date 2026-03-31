"""Extracted region-detection helpers for image_composite_converter.

This module contains the first refactoring slice for splitting the monolithic
converter script into smaller ~100-line blocks.
"""

from __future__ import annotations

import csv
import json
import os
from collections.abc import Callable

ANNOTATION_COLORS: dict[str, tuple[int, int, int]] = {
    "circle": (0, 0, 255),
    "stem": (0, 180, 0),
    "text": (255, 0, 0),
}


def _expand_bbox(bbox: tuple[int, int, int, int], width: int, height: int, pad: int = 1) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = bbox
    return (
        max(0, int(x0) - pad),
        max(0, int(y0) - pad),
        min(width - 1, int(x1) + pad),
        min(height - 1, int(y1) + pad),
    )


def _bbox_to_dict(label: str, bbox: tuple[int, int, int, int], color: tuple[int, int, int]) -> dict[str, object]:
    x0, y0, x1, y1 = bbox
    return {
        "label": label,
        "bbox": {
            "x0": int(x0),
            "y0": int(y0),
            "x1": int(x1),
            "y1": int(y1),
            "width": int(x1 - x0 + 1),
            "height": int(y1 - y0 + 1),
        },
        "color_bgr": [int(color[0]), int(color[1]), int(color[2])],
    }


def detectRelevantRegionsImpl(img, cv2_module, np_module) -> list[dict[str, object]]:
    if cv2_module is None or np_module is None:
        raise RuntimeError("detect_relevant_regions benötigt numpy und opencv-python-headless")
    if img is None:
        return []

    height, width = img.shape[:2]
    gray = cv2_module.cvtColor(img, cv2_module.COLOR_BGR2GRAY)
    blur = cv2_module.GaussianBlur(gray, (5, 5), 0)
    _thr, binary_inv = cv2_module.threshold(blur, 0, 255, cv2_module.THRESH_BINARY_INV + cv2_module.THRESH_OTSU)
    regions: list[dict[str, object]] = []
    used_mask = np_module.zeros((height, width), dtype=np_module.uint8)

    circles = cv2_module.HoughCircles(
        blur,
        cv2_module.HOUGH_GRADIENT,
        dp=1.2,
        minDist=max(8, min(height, width) // 4),
        param1=120,
        param2=12,
        minRadius=max(3, min(height, width) // 10),
        maxRadius=max(4, min(height, width) // 2),
    )
    if circles is not None:
        best = max(circles[0], key=lambda c: float(c[2]))
        cx, cy, radius = [int(round(v)) for v in best]
        radius = max(1, radius)
        circle_mask = np_module.zeros((height, width), dtype=np_module.uint8)
        cv2_module.circle(circle_mask, (cx, cy), radius + 1, 255, thickness=-1)
        bbox = _expand_bbox((cx - radius, cy - radius, cx + radius, cy + radius), width, height, pad=1)
        regions.append(_bbox_to_dict("circle", bbox, ANNOTATION_COLORS["circle"]))
        used_mask = cv2_module.bitwise_or(used_mask, circle_mask)

    residual = cv2_module.bitwise_and(binary_inv, cv2_module.bitwise_not(used_mask))
    num_labels, _labels, stats, _centroids = cv2_module.connectedComponentsWithStats(residual, connectivity=8)
    stem_candidate = None
    text_candidates: list[tuple[int, int, int, int]] = []
    for idx in range(1, num_labels):
        x, y, w, h, area = [int(v) for v in stats[idx]]
        if area < 6:
            continue
        bbox = (x, y, x + w - 1, y + h - 1)
        aspect = max(w, h) / max(1.0, min(w, h))
        touches_circle = False
        if regions:
            circle_bbox = regions[0]["bbox"]
            cx0 = int(circle_bbox["x0"])
            cy0 = int(circle_bbox["y0"])
            cx1 = int(circle_bbox["x1"])
            cy1 = int(circle_bbox["y1"])
            touches_circle = not (bbox[2] < cx0 - 2 or bbox[0] > cx1 + 2 or bbox[3] < cy0 - 2 or bbox[1] > cy1 + 2)
        if stem_candidate is None and touches_circle and aspect >= 2.2:
            stem_candidate = bbox
            continue
        text_candidates.append(bbox)

    if stem_candidate is not None:
        regions.append(_bbox_to_dict("stem", _expand_bbox(stem_candidate, width, height, pad=1), ANNOTATION_COLORS["stem"]))
    if text_candidates:
        x0 = min(b[0] for b in text_candidates)
        y0 = min(b[1] for b in text_candidates)
        x1 = max(b[2] for b in text_candidates)
        y1 = max(b[3] for b in text_candidates)
        regions.append(_bbox_to_dict("text", _expand_bbox((x0, y0, x1, y1), width, height, pad=1), ANNOTATION_COLORS["text"]))
    return regions


def annotateImageRegionsImpl(img, regions: list[dict[str, object]], cv2_module):
    if cv2_module is None:
        raise RuntimeError("annotate_image_regions benötigt opencv-python-headless")
    annotated = img.copy()
    for region in regions:
        bbox = dict(region["bbox"])
        color = tuple(int(v) for v in region["color_bgr"])
        label = str(region["label"])
        x0, y0, x1, y1 = int(bbox["x0"]), int(bbox["y0"]), int(bbox["x1"]), int(bbox["y1"])
        cv2_module.rectangle(annotated, (x0, y0), (x1, y1), color, thickness=2)
        cv2_module.putText(
            annotated, label, (x0, max(12, y0 - 4)), cv2_module.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2_module.LINE_AA
        )
    return annotated


def analyzeRangeImpl(
    folder_path: str,
    output_root: str | None,
    start_ref: str,
    end_ref: str,
    default_output_root_fn: Callable[[], str],
    in_requested_range_fn: Callable[[str, str, str], bool],
    detect_regions_fn: Callable[[object], list[dict[str, object]]],
    annotate_regions_fn: Callable[[object, list[dict[str, object]]], object],
    cv2_module,
    np_module,
) -> str:
    out_root = output_root or os.path.join(default_output_root_fn(), "annotated")
    annotated_dir = os.path.join(out_root, "annotated_pngs")
    reports_dir = os.path.join(out_root, "reports")
    os.makedirs(annotated_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)
    files = sorted(
        f
        for f in os.listdir(folder_path)
        if f.lower().endswith((".bmp", ".jpg", ".jpeg", ".png", ".gif")) and in_requested_range_fn(f, start_ref, end_ref)
    )
    report_rows: list[dict[str, object]] = []
    for filename in files:
        image_path = os.path.join(folder_path, filename)
        stem = os.path.splitext(filename)[0]
        if cv2_module is None or np_module is None:
            report_rows.append({"filename": filename, "status": "missing_dependencies", "regions": []})
            continue
        img = cv2_module.imread(image_path)
        if img is None:
            report_rows.append({"filename": filename, "status": "unreadable", "regions": []})
            continue
        regions = detect_regions_fn(img)
        annotated = annotate_regions_fn(img, regions)
        cv2_module.imwrite(os.path.join(annotated_dir, f"{stem}_annotated.png"), annotated)
        report_rows.append({"filename": filename, "status": "ok", "regions": regions})

    json_path = os.path.join(reports_dir, "detected_regions.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_rows, f, ensure_ascii=False, indent=2)
    csv_path = os.path.join(reports_dir, "detected_regions.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["filename", "label", "x0", "y0", "x1", "y1", "width", "height", "color_bgr", "status"])
        for row in report_rows:
            if not row["regions"]:
                writer.writerow([row["filename"], "", "", "", "", "", "", "", "", row["status"]])
                continue
            for region in row["regions"]:
                bbox = region["bbox"]
                writer.writerow(
                    [
                        row["filename"],
                        region["label"],
                        bbox["x0"],
                        bbox["y0"],
                        bbox["x1"],
                        bbox["y1"],
                        bbox["width"],
                        bbox["height"],
                        ",".join(str(int(v)) for v in region["color_bgr"]),
                        row["status"],
                    ]
                )
    return out_root


# Backward-compatible aliases
_expand_bbox = _expand_bbox
_bbox_to_dict = _bbox_to_dict
detectRelevantRegionsImpl = detectRelevantRegionsImpl
annotateImageRegionsImpl = annotateImageRegionsImpl
analyzeRangeImpl = analyzeRangeImpl
