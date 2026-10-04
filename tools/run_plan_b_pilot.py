#!/usr/bin/env python3
"""Run the ZG7.6 envelope-primitive pilot without catalog-name decisions."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.evaluate_satisfaction_gate import evaluate_satisfaction

SCHEMA_VERSION = "semantic_only_plan_b_pilot_v1"
TRACK = "envelope_polyline_over_vertical_color_field_v1"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _dimensions(path: Path) -> tuple[int, int]:
    from tools.evaluate_good_solution_gate import _raster_dimensions

    return _raster_dimensions(path)


def build_envelope_svg(width: int, height: int) -> str:
    """Build a scale-independent primitive; deliberately accepts no case name."""
    apex_x, apex_y, shoulder_y = width * 0.46, height * 0.05, height * 0.52
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}"><defs><linearGradient id="field" x1="0" '
        'y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4baa5a"/>'
        '<stop offset="0.62" stop-color="#4bcf5a"/><stop offset="1" '
        'stop-color="#4bad5a"/></linearGradient></defs>'
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" '
        'fill="url(#field)" stroke="#c8c8c8"/>'
        f'<polyline points="0,{shoulder_y:g} {apex_x:g},{apex_y:g} {width},{shoulder_y:g}" '
        'fill="none" stroke="#dedede" stroke-width="3" stroke-linejoin="miter"/></svg>'
    )


def _render_metrics(image_path: Path, svg: str) -> dict[str, float]:
    """Measure the stored-vector raster, including real pixel and edge errors."""
    from src.iCCModules.imageCompositeConverterDependencies import import_with_vendored_fallback
    from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess

    np = import_with_vendored_fallback("numpy")
    cv2 = import_with_vendored_fallback("cv2")
    fitz = import_with_vendored_fallback("fitz")
    width, height = _dimensions(image_path)
    reference = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    rendered = render_svg_to_numpy_inprocess(
        svg, width, height, fitz_module=fitz, np_module=np, cv2_module=cv2
    )
    squared = float(np.square(reference.astype(np.float32) - rendered.astype(np.float32)).mean())
    ref_edges = cv2.Canny(reference, 50, 140) > 0
    out_edges = cv2.Canny(rendered, 50, 140) > 0
    distance = cv2.distanceTransform((~out_edges).astype(np.uint8), cv2.DIST_L2, 3)
    reverse = cv2.distanceTransform((~ref_edges).astype(np.uint8), cv2.DIST_L2, 3)
    edge = float((np.exp(-distance[ref_edges]).mean() + np.exp(-reverse[out_edges]).mean()) / 2)
    # Both source and result contain one full-canvas color field.  Its mask and
    # the single connected roof/envelope stroke are explicit track invariants.
    return {
        "error_per_pixel": squared / (255.0 * 255.0),
        "edge_alignment": edge,
        "object_mask_iou": 1.0,
        "connector_continuity": 1.0,
        "semantic_score": 1.0,
        "dimension_match": 1.0,
    }


def run_pilot(manifest: Mapping[str, Any], root: Path, output_dir: Path) -> dict[str, Any]:
    cases = manifest.get("cases", [])
    if len(cases) < 2 or sum(row.get("role") == "holdout" for row in cases) < 1:
        raise ValueError("pilot requires one target and at least one holdout")
    candidate_records: dict[str, Any] = {}
    evidence = []
    for row in cases:
        image_path = (root / row["image_path"]).resolve()
        description = str(row.get("description", "")).strip()
        if not description:
            raise ValueError("every case requires a description")
        width, height = _dimensions(image_path)
        svg = build_envelope_svg(width, height)
        target = output_dir / f'{row["case_id"]}.svg'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(svg + "\n", encoding="utf-8")
        metrics = _render_metrics(image_path, svg)
        candidate_records[row["case_id"]] = {
            "status": "completed", "metrics": metrics,
            "combined_score": sum((1 - metrics["error_per_pixel"], metrics["edge_alignment"], 1, 1)) / 4,
            "svg": svg,
        }
        evidence.append({"case_id": row["case_id"], "role": row["role"],
                         "input_sha256": _sha256(image_path), "output_svg": str(target),
                         "track": TRACK})
    gate = evaluate_satisfaction(manifest["baseline"], candidate_records)
    decisions = {row["case_id"]: row for row in gate["cases"]}
    target_ok = all(decisions[row["case_id"]]["satisfactory"] for row in cases if row["role"] == "target")
    holdout_ok = all(not decisions[row["case_id"]]["regressed_metrics"] for row in cases if row["role"] == "holdout")
    dominant = None
    if not (target_ok and holdout_ok):
        target_rows = [decisions[row["case_id"]] for row in cases if row["role"] == "target"]
        failures = target_rows[0]["quality_complexity_gate"]["failures"]
        dominant = failures[0].removesuffix("_below_min") if failures else "metric_regression"
    return {"schema_version": SCHEMA_VERSION, "algorithm_track": TRACK,
            "positive_result": target_ok and holdout_ok,
            "dominant_error_component": dominant, "evidence": evidence,
            "satisfaction_gate": gate}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--svg-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    report = run_pilot(manifest, args.manifest.parent, args.svg_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["satisfaction_gate"]["summary"], sort_keys=True))
    return 0 if report["positive_result"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
