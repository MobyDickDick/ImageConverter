#!/usr/bin/env python3
"""Compare a frozen ZG7 baseline and apply both hard satisfaction gates."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.evaluate_good_solution_gate import evaluate_good_solution
from tools.evaluate_quality_complexity_gate import evaluate_quality_complexity_gate

SCHEMA_VERSION = "semantic_only_satisfaction_report_v1"
BASELINE_SCHEMA_VERSION = "semantic_only_baseline_manifest_v1"
LOWER_IS_BETTER = {"error_per_pixel"}
HIGHER_IS_BETTER = {
    "edge_alignment",
    "object_mask_iou",
    "connector_continuity",
    "semantic_score",
    "dimension_match",
}


def canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def seal_baseline_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy carrying a digest over all immutable baseline fields."""
    result = dict(manifest)
    result.pop("baseline_sha256", None)
    result["baseline_sha256"] = canonical_sha256(result)
    return result


def _validate_baseline(manifest: Mapping[str, Any]) -> None:
    if manifest.get("schema_version") != BASELINE_SCHEMA_VERSION:
        raise ValueError("unsupported baseline schema_version")
    digest = manifest.get("baseline_sha256")
    unsigned = dict(manifest)
    unsigned.pop("baseline_sha256", None)
    if not isinstance(digest, str) or digest != canonical_sha256(unsigned):
        raise ValueError("baseline_sha256 mismatch")
    provenance = manifest.get("provenance", {})
    for field in ("commit", "seed", "toolchain", "input_hashes"):
        if field not in provenance:
            raise ValueError(f"missing baseline provenance:{field}")


def _classify_metric(name: str, before: object, after: object) -> str:
    if isinstance(before, bool) or isinstance(after, bool):
        raise ValueError(f"metric {name} must be numeric")
    try:
        old, new = float(before), float(after)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"metric {name} must be numeric") from exc
    if name in LOWER_IS_BETTER:
        delta = old - new
    elif name in HIGHER_IS_BETTER:
        delta = new - old
    else:
        raise ValueError(f"metric direction is not defined:{name}")
    return "improved" if delta > 1e-12 else "regressed" if delta < -1e-12 else "unchanged"


def _svg_dimensions_match(svg_text: str, expected: Mapping[str, Any]) -> bool:
    try:
        root = ET.fromstring(svg_text)
        width = float(str(root.get("width", "")).removesuffix("px"))
        height = float(str(root.get("height", "")).removesuffix("px"))
        return width == float(expected["width"]) and height == float(expected["height"])
    except (ET.ParseError, KeyError, TypeError, ValueError):
        return False


def evaluate_satisfaction(
    baseline_manifest: Mapping[str, Any], candidate_records: Mapping[str, Any]
) -> dict[str, Any]:
    """Build deterministic before/after and independent gate decisions."""
    _validate_baseline(baseline_manifest)
    baseline_cases = baseline_manifest.get("cases")
    if not isinstance(baseline_cases, dict):
        raise ValueError("baseline cases must be an object")
    unknown = sorted(set(candidate_records) - set(baseline_cases))
    missing = sorted(set(baseline_cases) - set(candidate_records))
    if unknown or missing:
        raise ValueError(f"case mismatch (missing={missing}, unknown={unknown})")

    cases: list[dict[str, Any]] = []
    for case_id in sorted(baseline_cases):
        baseline = baseline_cases[case_id]
        candidate = candidate_records[case_id]
        before = baseline.get("metrics", {})
        after = candidate.get("metrics", {})
        if set(before) != set(after):
            raise ValueError(f"metric mismatch:{case_id}")
        comparison = {
            name: _classify_metric(name, before[name], after[name])
            for name in sorted(before)
        }
        regressed = [name for name, value in comparison.items() if value == "regressed"]
        improved_metrics = [
            name for name, value in comparison.items() if value == "improved"
        ]
        svg_text = str(candidate.get("svg", ""))
        dimensions_match = _svg_dimensions_match(svg_text, baseline["dimensions"])
        good_metrics = {
            "error_per_pixel": after.get("error_per_pixel"),
            "semantic_score": after.get("semantic_score"),
            "dimension_match": after.get("dimension_match") if dimensions_match else 0.0,
        }
        good_gate = evaluate_good_solution(
            good_metrics, source_status=str(candidate.get("status", ""))
        )
        complexity_metrics = {
            "pixel_similarity": 1.0 - float(after.get("error_per_pixel", 1.0)),
            "edge_alignment": float(after.get("edge_alignment", 0.0)),
            "structure_score": float(after.get("object_mask_iou", 0.0)),
            "semantic_score": float(after.get("semantic_score", 0.0)),
            "combined_score": float(candidate.get("combined_score", 0.0)),
        }
        quality_complexity_gate = evaluate_quality_complexity_gate(
            complexity_metrics, svg_text
        )
        hard_rejections = []
        if not dimensions_match:
            hard_rejections.append("svg_dimension_mismatch")
        hard_rejections.extend(quality_complexity_gate["failures"])
        technically_completed = str(candidate.get("status")) == "completed"
        improved = bool(improved_metrics) and not regressed
        satisfactory = (
            technically_completed
            and not regressed
            and not hard_rejections
            and good_gate["status"] == "good"
            and quality_complexity_gate["passed"]
        )
        cases.append(
            {
                "case_id": case_id,
                "before": before,
                "after": after,
                "metric_classification": comparison,
                "regressed_metrics": regressed,
                "improved_metrics": improved_metrics,
                "technically_completed": technically_completed,
                "improved": improved,
                "satisfactory": satisfactory,
                "hard_rejections": sorted(set(hard_rejections)),
                "good_solution_gate": good_gate,
                "quality_complexity_gate": quality_complexity_gate,
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "baseline_sha256": baseline_manifest["baseline_sha256"],
        "provenance": baseline_manifest["provenance"],
        "summary": {
            "case_count": len(cases),
            "technically_completed": sum(row["technically_completed"] for row in cases),
            "improved": sum(row["improved"] for row in cases),
            "satisfactory": sum(row["satisfactory"] for row in cases),
        },
        "cases": cases,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
        report = evaluate_satisfaction(baseline, candidate["cases"])
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    serialized = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
