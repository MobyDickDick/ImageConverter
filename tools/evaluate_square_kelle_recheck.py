"""Re-render frozen before/after square-and-stem SVGs and apply hard gates."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import fitz
import numpy as np

from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from tools.evaluate_satisfaction_gate import evaluate_satisfaction, seal_baseline_manifest
from tools.review_conversion_quality import normalized_mse


def _square_and_stem_semantics(root: ET.Element) -> float:
    """Check the described topology from geometry, independently of element IDs."""
    vectors = [element for element in root.iter() if element.tag.rsplit("}", 1)[-1] in {"rect", "path", "circle", "text", "image", "line", "polygon", "polyline", "ellipse"}]
    if sorted(element.tag.rsplit("}", 1)[-1] for element in vectors) != ["path", "rect"]:
        return 0.0
    rect = next(element for element in vectors if element.tag.endswith("rect"))
    stem = next(element for element in vectors if element.tag.endswith("path"))
    match = re.fullmatch(r"M\s+([-\d.]+)\s+([-\d.]+)\s+L\s+([-\d.]+)\s+([-\d.]+)", stem.get("d", ""))
    if not match:
        return 0.0
    x0, y0, x1, y1 = map(float, match.groups())
    x, y, width, height = (float(rect.get(key, "0")) for key in ("x", "y", "width", "height"))
    tolerance = float(rect.get("stroke-width", "0")) / 2 + 1e-4
    return float(
        width > 0 and height > 0 and abs(x0 - x1) < 1e-4
        and abs(x1 - (x + width / 2)) <= width * 0.1
        and y0 < y and abs(y1 - y) <= tolerance
        and 0.7 <= width / height <= 1.3
    )


def measure(image_path: Path, svg_path: Path) -> dict:
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Unreadable raster: {image_path}")
    height, width = image.shape[:2]
    svg = svg_path.read_text(encoding="utf-8")
    root = ET.fromstring(svg)
    rendered = render_svg_to_numpy_inprocess(
        svg, width, height, fitz_module=fitz, np_module=np, cv2_module=cv2
    )
    if rendered is None:
        raise ValueError(f"Unrenderable SVG: {svg_path}")
    ref_edges = cv2.Canny(image, 50, 140) > 0
    out_edges = cv2.Canny(rendered, 50, 140) > 0
    distance = cv2.distanceTransform((~out_edges).astype(np.uint8), cv2.DIST_L2, 3)
    reverse = cv2.distanceTransform((~ref_edges).astype(np.uint8), cv2.DIST_L2, 3)
    edge = (
        float((np.exp(-distance[ref_edges]).mean() + np.exp(-reverse[out_edges]).mean()) / 2)
        if ref_edges.any() and out_edges.any()
        else 0.0
    )
    ref_mask = np.min(image, axis=2) < 210
    out_mask = np.min(rendered, axis=2) < 210
    union = int((ref_mask | out_mask).sum())
    iou = float((ref_mask & out_mask).sum() / union) if union else 1.0
    # This contract measures the described unlabelled square and stem. It does
    # not claim recognition of an undescribed marking in the raster interior.
    semantic = _square_and_stem_semantics(root)
    dimension = float(
        float(root.get("width", "0").removesuffix("px")) == width
        and float(root.get("height", "0").removesuffix("px")) == height
    )
    mean_delta2, mse = normalized_mse(image, rendered)
    metrics = {"error_per_pixel": mse, "edge_alignment": edge, "object_mask_iou": iou, "semantic_score": semantic, "dimension_match": dimension}
    return {"status": "completed", "svg": svg, "metrics": metrics, "mean_delta2": mean_delta2, "combined_score": (1 - mse + edge + iou + semantic) / 4, "dimensions": {"width": width, "height": height}, "svg_sha256": hashlib.sha256(svg_path.read_bytes()).hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    root = args.manifest.parent
    before, after, evidence = {}, {}, []
    for case in manifest["cases"]:
        image_path = root / case["image"]
        old = measure(image_path, root / case["before_svg"])
        new = measure(image_path, root / case["after_svg"])
        before[case["case_id"]] = {"metrics": old["metrics"], "dimensions": old["dimensions"]}
        after[case["case_id"]] = new
        evidence.append({**case, "input_sha256": hashlib.sha256(image_path.read_bytes()).hexdigest(), "before_mean_delta2": old["mean_delta2"], "after_mean_delta2": new["mean_delta2"], "before_svg_sha256": old["svg_sha256"], "after_svg_sha256": new["svg_sha256"]})
    provenance = {
        **manifest["provenance"],
        "input_hashes": {row["case_id"]: row["input_sha256"] for row in evidence},
    }
    baseline = seal_baseline_manifest({"schema_version": "semantic_only_baseline_manifest_v1", "provenance": provenance, "cases": before})
    report = {"schema_version": "square_kelle_recheck_v1", "baseline": baseline, "evidence": evidence, "satisfaction_gate": evaluate_satisfaction(baseline, after), "semantic_contract": "unlabelled square and connector; interior marking remains a quality follow-up", "measurement": {"foreground_threshold": 210, "canny_thresholds": [50, 140], "output": "saved SVG re-rendered with the production renderer"}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["satisfaction_gate"]["summary"], sort_keys=True))
    return 0 if all(case["satisfactory"] for case in report["satisfaction_gate"]["cases"]) else 2


if __name__ == "__main__":
    raise SystemExit(main())
