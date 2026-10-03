#!/usr/bin/env python3
"""Classify converter results with the versioned Good-Solution-Gate v1."""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping
from xml.etree import ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.iCCModules.imageCompositeConverterReachability import (
    aggregateNotReachableExitCodeImpl,
    classifyNotReachableImpl,
)


SCHEMA_VERSION = "good_solution_gate_v1"
STATUSES = ("good", "suboptimal", "not_reachable")
DEFAULT_THRESHOLDS: dict[str, float] = {
    "max_error_per_pixel": 0.05,
    "min_semantic_score": 0.85,
    "min_dimension_match": 0.99,
}
NOT_REACHABLE_SOURCE_STATUSES = {
    "budget_exceeded",
    "conversion_failed",
    "dimension_violation",
    "not_reachable",
    "semantic_conflict",
    "semantic_mismatch",
    "semantic_rejected",
    "stagnation",
}
REQUIRED_METRICS = ("error_per_pixel", "semantic_score", "dimension_match")
METRIC_HIERARCHY = {
    "primary": ("semantic_score", "dimension_match"),
    "secondary": ("error_per_pixel",),
}
_SVG_LENGTH = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*(?:px)?\s*$", re.IGNORECASE)


def _match_ratio(expected: float, actual: float) -> float:
    if expected <= 0 or actual <= 0:
        return 0.0
    return min(expected, actual) / max(expected, actual)


def _raster_dimensions(image_path: Path) -> tuple[int, int]:
    """Read PNG/JPEG dimensions without adding a runtime image dependency."""
    data = image_path.read_bytes()
    if len(data) >= 24 and data[:8] == b"\x89PNG\r\n\x1a\n":
        width = int.from_bytes(data[16:20], "big")
        height = int.from_bytes(data[20:24], "big")
        if width > 0 and height > 0:
            return width, height
        raise ValueError("invalid PNG dimensions")

    if len(data) < 4 or data[:2] != b"\xff\xd8":
        raise ValueError("unsupported raster format")
    offset = 2
    sof_markers = {
        0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
        0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF,
    }
    while offset + 1 < len(data):
        if data[offset] != 0xFF:
            offset += 1
            continue
        marker = data[offset + 1]
        offset += 2
        if marker in {0xD8, 0xD9, 0x01} or 0xD0 <= marker <= 0xD7:
            continue
        if offset + 1 >= len(data):
            break
        segment_length = int.from_bytes(data[offset : offset + 2], "big")
        if segment_length < 2 or offset + segment_length > len(data):
            break
        if marker in sof_markers and segment_length >= 7:
            height = int.from_bytes(data[offset + 3 : offset + 5], "big")
            width = int.from_bytes(data[offset + 5 : offset + 7], "big")
            if width > 0 and height > 0:
                return width, height
            raise ValueError("invalid JPEG dimensions")
        offset += segment_length
    raise ValueError("could not parse JPEG dimensions")


def measure_dimension_fidelity(image_path: Path, svg_path: Path) -> dict[str, Any]:
    """Measure SVG canvas width, height and aspect ratio against a raster source."""
    raster_width, raster_height = _raster_dimensions(image_path)

    root = ElementTree.parse(svg_path).getroot()
    dimensions: list[float] = []
    for attribute in ("width", "height"):
        match = _SVG_LENGTH.fullmatch(root.get(attribute, ""))
        dimensions.append(float(match.group(1)) if match else 0.0)
    svg_width, svg_height = dimensions
    if not svg_width or not svg_height:
        view_box = root.get("viewBox", "").replace(",", " ").split()
        if len(view_box) == 4:
            try:
                svg_width, svg_height = float(view_box[2]), float(view_box[3])
            except ValueError:
                svg_width = svg_height = 0.0

    width_match = _match_ratio(raster_width, svg_width)
    height_match = _match_ratio(raster_height, svg_height)
    raster_aspect = raster_width / raster_height
    svg_aspect = svg_width / svg_height if svg_height else 0.0
    aspect_ratio_match = _match_ratio(raster_aspect, svg_aspect)
    return {
        "raster": {"width": raster_width, "height": raster_height, "aspect_ratio": raster_aspect},
        "svg": {"width": svg_width, "height": svg_height, "aspect_ratio": svg_aspect},
        "width_match": width_match,
        "height_match": height_match,
        "aspect_ratio_match": aspect_ratio_match,
        "dimension_match": min(width_match, height_match, aspect_ratio_match),
    }


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if number == number and abs(number) != float("inf") else None


def evaluate_good_solution(
    metrics: Mapping[str, Any],
    *,
    source_status: str | None = None,
    thresholds: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    """Return one deterministic status, including all evidence for the decision."""
    limits = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    normalized = {name: _finite_number(metrics.get(name)) for name in REQUIRED_METRICS}
    reasons: list[str] = []
    normalized_source_status = str(source_status or "").strip().lower()

    if normalized_source_status in NOT_REACHABLE_SOURCE_STATUSES:
        reasons.append(f"source_status:{normalized_source_status}")
    reasons.extend(f"missing_metric:{name}" for name, value in normalized.items() if value is None)
    if reasons:
        status = "not_reachable"
    else:
        assert all(value is not None for value in normalized.values())
        # Primary constraints are evaluated first and cannot be compensated by
        # an excellent pixel score.  The pixel metric only refines results that
        # already satisfy semantics and dimensions.
        if normalized["semantic_score"] < limits["min_semantic_score"]:
            reasons.append("semantic_score_below_min")
        if normalized["dimension_match"] < limits["min_dimension_match"]:
            reasons.append("dimension_match_below_min")
        if not reasons and normalized["error_per_pixel"] > limits["max_error_per_pixel"]:
            reasons.append("error_per_pixel_above_max")
        status = "suboptimal" if reasons else "good"

    reachability = (
        classifyNotReachableImpl(
            {
                "status": normalized_source_status,
                # A failed physical dimension check has stronger evidence than
                # the generic missing-metric fallback.
                "reason": "dimension_violation"
                if "missing_metric:dimension_match" in reasons
                else "",
            }
        )
        if status == "not_reachable"
        else None
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "reasons": reasons or ["all_thresholds_satisfied"],
        "metrics": normalized,
        "thresholds": limits,
        "metric_hierarchy": {name: list(metrics) for name, metrics in METRIC_HIERARCHY.items()},
        "decision_tier": (
            "reachability"
            if status == "not_reachable"
            else "primary"
            if any(reason in {"semantic_score_below_min", "dimension_match_below_min"} for reason in reasons)
            else "secondary"
            if status == "suboptimal"
            else "all"
        ),
        "reachability": reachability,
    }


def build_good_solution_report(
    rows: Mapping[str, Any],
    *,
    thresholds: Mapping[str, float] | None = None,
    image_dir: Path | None = None,
    svg_dir: Path | None = None,
) -> dict[str, Any]:
    """Classify every result-map row and return a machine-readable report."""
    evaluations: list[dict[str, Any]] = []
    for map_name, raw_row in sorted(rows.items()):
        row = raw_row if isinstance(raw_row, dict) else {}
        filename = str(row.get("filename") or map_name)
        metrics = dict(row)
        dimension_evidence = None
        if image_dir is not None and svg_dir is not None:
            image_path = image_dir / filename
            svg_path = svg_dir / f"{Path(filename).stem}.svg"
            try:
                dimension_evidence = measure_dimension_fidelity(image_path, svg_path)
                metrics["dimension_match"] = dimension_evidence["dimension_match"]
            except (OSError, ElementTree.ParseError, ValueError):
                metrics["dimension_match"] = None
        result = evaluate_good_solution(
            metrics,
            source_status=str(row.get("status") or ""),
            thresholds=thresholds,
        )
        evaluations.append({"filename": filename, **result, "dimension_evidence": dimension_evidence})
    counts = Counter(item["status"] for item in evaluations)
    return {
        "schema_version": SCHEMA_VERSION,
        "statuses": list(STATUSES),
        "thresholds": {**DEFAULT_THRESHOLDS, **(thresholds or {})},
        "metric_hierarchy": {name: list(metrics) for name, metrics in METRIC_HIERARCHY.items()},
        "summary": {"file_count": len(evaluations), **{name: counts[name] for name in STATUSES}},
        "evaluations": evaluations,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result_map", type=Path, help="conversion_result_map.json to classify")
    parser.add_argument("--output", type=Path, help="write the report in addition to stdout")
    parser.add_argument("--image-dir", type=Path, help="source raster directory for hard dimension checks")
    parser.add_argument("--svg-dir", type=Path, help="converted SVG directory for hard dimension checks")
    parser.add_argument(
        "--fail-on-not-reachable",
        action="store_true",
        help="return the canonical 20..23 exit code when the report contains unreachable results",
    )
    args = parser.parse_args(argv)
    try:
        rows = json.loads(args.result_map.read_text(encoding="utf-8"))
        if not isinstance(rows, dict):
            raise ValueError("result map must be a JSON object")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))
    if (args.image_dir is None) != (args.svg_dir is None):
        parser.error("--image-dir and --svg-dir must be supplied together")
    report = build_good_solution_report(rows, image_dir=args.image_dir, svg_dir=args.svg_dir)
    serialized = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    if args.fail_on_not_reachable:
        unreachable = [row["reachability"] for row in report["evaluations"] if row["reachability"]]
        return aggregateNotReachableExitCodeImpl(unreachable)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
