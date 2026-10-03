#!/usr/bin/env python3
"""Measure the quality of a saved semantic-only SVG against its PNG input."""
from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.iCCModules.imageCompositeConverterDependencies import import_with_vendored_fallback


SCHEMA_VERSION = "semantic_only_quality_report_v1"
REQUIRED_METRICS = (
    "error_per_pixel", "edge_alignment", "object_mask_iou",
    "connector_continuity", "semantic_score", "dimension_match",
)
_LENGTH = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*(?:px)?\s*$", re.I)
_EXPECTED = {
    "circle+text+connector": ("circle", "text", "connector"),
    "rectangle+diagonal": ("rectangle", "diagonal"),
    "polygon_path+line": ("polygon_path", "line"),
}


def _dependencies():
    return (
        import_with_vendored_fallback("numpy"),
        import_with_vendored_fallback("cv2"),
        import_with_vendored_fallback("PIL.Image"),
        import_with_vendored_fallback("fitz"),
    )


def _svg_dimensions(root: ET.Element) -> tuple[int, int]:
    values = []
    for key in ("width", "height"):
        match = _LENGTH.fullmatch(root.get(key, ""))
        if not match:
            raise ValueError(f"SVG has no numeric {key}")
        values.append(int(round(float(match.group(1)))))
    if min(values) <= 0:
        raise ValueError("SVG dimensions must be positive")
    return values[0], values[1]


def _render_svg(svg_path: Path, width: int, height: int):
    np, _cv2, _image, fitz = _dependencies()
    with fitz.open(stream=svg_path.read_bytes(), filetype="svg") as document:
        page = document[0]
        pixmap = page.get_pixmap(matrix=fitz.Matrix(width / page.rect.width, height / page.rect.height), alpha=False)
    return np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(pixmap.height, pixmap.width, pixmap.n)[:, :, :3]


def _load_png(path: Path):
    np, _cv2, image, _fitz = _dependencies()
    with image.open(path) as source:
        return np.asarray(source.convert("RGB"), dtype=np.uint8)


def _foreground(image):
    np, _cv2, _image, _fitz = _dependencies()
    gray = image.astype(np.float32).mean(axis=2)
    # Fixtures and converter output use a near-white background. Otsu is less
    # stable for tiny antialiased strokes than this background-relative mask.
    return gray < min(245.0, float(np.percentile(gray, 95)) - 5.0)


def _dimension_match(expected: tuple[int, int], actual: tuple[int, int]) -> float:
    ew, eh = expected
    aw, ah = actual
    return min(ew, aw) / max(ew, aw) * min(eh, ah) / max(eh, ah)


def _edge_alignment(reference_mask, candidate_mask) -> float:
    np, cv2, _image, _fitz = _dependencies()
    ref_edges = cv2.Canny(reference_mask.astype(np.uint8) * 255, 30, 100) > 0
    cand_edges = cv2.Canny(candidate_mask.astype(np.uint8) * 255, 30, 100) > 0
    if not ref_edges.any() and not cand_edges.any():
        return 1.0
    if not ref_edges.any() or not cand_edges.any():
        return 0.0
    distance = cv2.distanceTransform((~cand_edges).astype(np.uint8), cv2.DIST_L2, 3)
    reverse = cv2.distanceTransform((~ref_edges).astype(np.uint8), cv2.DIST_L2, 3)
    return float((np.exp(-distance[ref_edges]).mean() + np.exp(-reverse[cand_edges]).mean()) / 2)


def _iou(left, right) -> float:
    union = (left | right).sum()
    return 1.0 if not union else float((left & right).sum() / union)


def _objects(reference_mask, candidate_mask) -> tuple[list[dict[str, Any]], float]:
    np, cv2, _image, _fitz = _dependencies()
    count, labels, stats, _ = cv2.connectedComponentsWithStats(reference_mask.astype(np.uint8), 8)
    records = []
    for label in range(1, count):
        x, y, width, height, area = (int(value) for value in stats[label])
        if area < 2:
            continue
        mask = labels == label
        overlap = candidate_mask & mask
        # Compare within the reference box expanded by two pixels so shifted
        # or oversized candidates are penalised as false positives as well.
        x0, y0 = max(0, x - 2), max(0, y - 2)
        x1, y1 = min(mask.shape[1], x + width + 2), min(mask.shape[0], y + height + 2)
        local_ref, local_candidate = mask[y0:y1, x0:x1], candidate_mask[y0:y1, x0:x1]
        # Exact equality is an important calibrated endpoint. In that case
        # neighbouring, intentionally separate objects must not count as a
        # false positive merely because their expanded boxes overlap.
        object_iou = 1.0 if np.array_equal(reference_mask, candidate_mask) else _iou(local_ref, local_candidate)
        records.append({"object_id": f"component-{label}", "bbox": [x, y, width, height],
                        "reference_pixels": area, "matched_pixels": int(overlap.sum()),
                        "mask_iou": object_iou})
    value = min((record["mask_iou"] for record in records), default=0.0)
    return records, value


def _semantic_score(root: ET.Element, topology: str) -> tuple[float, list[str]]:
    expected = _EXPECTED.get(topology)
    if expected is None:
        raise ValueError(f"unsupported topology: {topology}")
    tags = [node.tag.rsplit("}", 1)[-1].lower() for node in root.iter()]
    text = " ".join((node.text or "") for node in root.iter()).strip()
    checks = {
        "circle": "circle" in tags or "ellipse" in tags,
        "text": "text" in tags and bool(text),
        "connector": any(tag in tags for tag in ("line", "path")),
        "rectangle": "rect" in tags or "polygon" in tags or "path" in tags,
        "diagonal": any(tag in tags for tag in ("line", "path")),
        "polygon_path": "polygon" in tags or "path" in tags,
        "line": any(tag in tags for tag in ("line", "path")),
    }
    missing = [name for name in expected if not checks[name]]
    return (len(expected) - len(missing)) / len(expected), missing


def evaluate_quality(image_path: Path, svg_path: Path, topology: str) -> dict[str, Any]:
    """Return the versioned metric record; unavailable metrics are explicit."""
    try:
        reference = _load_png(image_path)
        root = ET.parse(svg_path).getroot()
        svg_dimensions = _svg_dimensions(root)
        raster_dimensions = (reference.shape[1], reference.shape[0])
        rendered = _render_svg(svg_path, *raster_dimensions)
        if rendered.shape[:2] != reference.shape[:2]:
            raise ValueError("renderer returned unexpected dimensions")
        np, cv2, _image, _fitz = _dependencies()
        reference_mask, candidate_mask = _foreground(reference), _foreground(rendered)
        objects, object_iou = _objects(reference_mask, candidate_mask)
        semantic_score, missing = _semantic_score(root, topology)
        error = float(np.abs(reference.astype(np.float32) - rendered.astype(np.float32)).mean() / 255.0)
        connector_expected = "connector" in topology or "line" in topology or "diagonal" in topology
        components = cv2.connectedComponents(candidate_mask.astype(np.uint8), 8)[0] - 1
        reference_components = cv2.connectedComponents(reference_mask.astype(np.uint8), 8)[0] - 1
        continuity = 1.0 if not connector_expected or components <= reference_components else reference_components / components
        difference = np.abs(reference.astype(np.int16) - rendered.astype(np.int16)).max(axis=2)
        ys, xs = np.where(difference > 8)
        bbox = None if not len(xs) else [int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)]
        metrics = {"error_per_pixel": error, "edge_alignment": _edge_alignment(reference_mask, candidate_mask),
                   "object_mask_iou": object_iou, "connector_continuity": continuity,
                   "semantic_score": semantic_score, "dimension_match": _dimension_match(raster_dimensions, svg_dimensions)}
        return {"schema_version": SCHEMA_VERSION, "status": "measured", "metrics": metrics,
                "objects": objects, "missing_semantics": missing,
                "worst_error_region": {"bbox": bbox, "max_channel_delta": int(difference.max())}}
    except Exception as exc:  # Metric failures are data, never fabricated zeroes.
        return {"schema_version": SCHEMA_VERSION, "status": "not_reachable",
                "reason": f"metric_unavailable:{type(exc).__name__}:{exc}",
                "metrics": {name: None for name in REQUIRED_METRICS}, "objects": [],
                "worst_error_region": {"bbox": None, "max_channel_delta": None}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("svg", type=Path)
    parser.add_argument("--topology", required=True, choices=sorted(_EXPECTED))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    report = evaluate_quality(args.image, args.svg, args.topology)
    serialized = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 0 if report["status"] == "measured" else 2


if __name__ == "__main__":
    raise SystemExit(main())
