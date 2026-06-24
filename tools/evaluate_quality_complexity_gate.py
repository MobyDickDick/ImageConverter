#!/usr/bin/env python3
"""Evaluate the IDO-20 SVG quality and complexity gate.

The gate combines raster similarity, edge alignment, structure, semantic score,
SVG element count, and path complexity.  It also rejects forbidden shortcuts such
as embedded raster copies even when their pixel score would be high.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from statistics import mean
from typing import Any
from xml.etree import ElementTree as ET

DEFAULT_THRESHOLDS: dict[str, float | int] = {
    "min_pixel_similarity": 0.78,
    "min_edge_alignment": 0.72,
    "min_structure_score": 0.72,
    "min_semantic_score": 0.85,
    "min_combined_score": 0.78,
    "max_svg_element_count": 80,
    "max_path_command_count": 160,
    "max_path_complexity_ratio": 4.0,
}
VECTOR_TAGS = {"circle", "ellipse", "line", "path", "polygon", "polyline", "rect", "text"}
PATH_COMMAND_RE = re.compile(r"[AaCcHhLlMmQqSsTtVvZz]")


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].casefold()


def analyze_svg_complexity(svg_text: str) -> dict[str, Any]:
    """Return catalog-free SVG complexity signals used by the gate."""
    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError as exc:
        return {
            "parse_error": str(exc),
            "embedded_raster_count": 0,
            "vector_element_count": 0,
            "path_count": 0,
            "path_command_count": 0,
            "path_complexity_ratio": float("inf"),
        }

    embedded_raster_count = 0
    vector_element_count = 0
    path_count = 0
    path_command_count = 0
    for element in root.iter():
        tag = _local_name(element.tag)
        if tag == "image":
            embedded_raster_count += 1
        if tag in VECTOR_TAGS:
            vector_element_count += 1
        if tag == "path":
            path_count += 1
            path_command_count += len(PATH_COMMAND_RE.findall(element.attrib.get("d", "")))
    denominator = max(1, vector_element_count)
    return {
        "parse_error": None,
        "embedded_raster_count": embedded_raster_count,
        "vector_element_count": vector_element_count,
        "path_count": path_count,
        "path_command_count": path_command_count,
        "path_complexity_ratio": round(path_command_count / denominator, 4),
    }


def evaluate_quality_complexity_gate(
    metrics: dict[str, float],
    svg_text: str,
    *,
    thresholds: dict[str, float | int] | None = None,
) -> dict[str, Any]:
    """Evaluate one SVG against the IDO-20 quality/complexity contract."""
    limits = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    complexity = analyze_svg_complexity(svg_text)
    failures: list[str] = []
    if complexity["parse_error"]:
        failures.append("svg_parse_error")
    if complexity["embedded_raster_count"] > 0:
        failures.append("embedded_raster_copy")
    metric_checks = {
        "pixel_similarity_below_min": metrics.get("pixel_similarity", 0.0) < float(limits["min_pixel_similarity"]),
        "edge_alignment_below_min": metrics.get("edge_alignment", 0.0) < float(limits["min_edge_alignment"]),
        "structure_score_below_min": metrics.get("structure_score", 0.0) < float(limits["min_structure_score"]),
        "semantic_score_below_min": metrics.get("semantic_score", 0.0) < float(limits["min_semantic_score"]),
        "combined_score_below_min": metrics.get("combined_score", 0.0) < float(limits["min_combined_score"]),
    }
    failures.extend(name for name, failed in metric_checks.items() if failed)
    if complexity["vector_element_count"] > int(limits["max_svg_element_count"]):
        failures.append("svg_element_count_above_max")
    if complexity["path_command_count"] > int(limits["max_path_command_count"]):
        failures.append("path_command_count_above_max")
    if complexity["path_complexity_ratio"] > float(limits["max_path_complexity_ratio"]):
        failures.append("path_complexity_ratio_above_max")
    return {
        "passed": not failures,
        "failures": failures,
        "metrics": {key: round(float(value), 4) for key, value in metrics.items()},
        "complexity": complexity,
        "thresholds": limits,
    }


def build_quality_complexity_gate_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    evaluations: list[dict[str, Any]] = []
    for row in rows:
        result = evaluate_quality_complexity_gate(row["metrics"], row["svg"])
        evaluations.append({"name": row["name"], **result})
    return {
        "schema_version": "quality_complexity_gate_v1",
        "thresholds": DEFAULT_THRESHOLDS,
        "acceptance_contract": {
            "rejects_embedded_raster_copies": True,
            "rejects_unnecessary_path_complexity": True,
            "rejects_semantically_wrong_pixel_near_results": True,
        },
        "summary": {
            "sample_count": len(evaluations),
            "passed_count": sum(1 for item in evaluations if item["passed"]),
            "failed_count": sum(1 for item in evaluations if not item["passed"]),
            "mean_combined_score": round(mean(item["metrics"].get("combined_score", 0.0) for item in evaluations), 4) if evaluations else 0.0,
        },
        "evaluations": evaluations,
    }


def _default_rows() -> list[dict[str, Any]]:
    good_metrics = {"pixel_similarity": 0.9, "edge_alignment": 0.86, "structure_score": 0.9, "semantic_score": 1.0, "combined_score": 0.91}
    return [{"name": "neutral_vector_badge", "metrics": good_metrics, "svg": '<svg xmlns="http://www.w3.org/2000/svg"><circle cx="8" cy="8" r="6"/><line x1="0" y1="8" x2="2" y2="8"/></svg>'}]


def write_quality_complexity_gate_report(output: Path, rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    report = build_quality_complexity_gate_report(rows or _default_rows())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("artifacts/evaluation/quality_complexity_gate_v1/quality_complexity_gate_v1.json"))
    args = parser.parse_args()
    report = write_quality_complexity_gate_report(args.output)
    print(json.dumps({"output": str(args.output), "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
