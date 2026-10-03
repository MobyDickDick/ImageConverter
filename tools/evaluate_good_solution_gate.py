#!/usr/bin/env python3
"""Classify converter results with the versioned Good-Solution-Gate v1."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = "good_solution_gate_v1"
STATUSES = ("good", "suboptimal", "not_reachable")
DEFAULT_THRESHOLDS: dict[str, float] = {
    "max_error_per_pixel": 0.05,
    "min_semantic_score": 0.85,
    "min_dimension_match": 0.99,
}
NOT_REACHABLE_SOURCE_STATUSES = {
    "conversion_failed",
    "not_reachable",
    "semantic_conflict",
    "semantic_mismatch",
    "semantic_rejected",
}
REQUIRED_METRICS = ("error_per_pixel", "semantic_score", "dimension_match")


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
        if normalized["error_per_pixel"] > limits["max_error_per_pixel"]:
            reasons.append("error_per_pixel_above_max")
        if normalized["semantic_score"] < limits["min_semantic_score"]:
            reasons.append("semantic_score_below_min")
        if normalized["dimension_match"] < limits["min_dimension_match"]:
            reasons.append("dimension_match_below_min")
        status = "suboptimal" if reasons else "good"

    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "reasons": reasons or ["all_thresholds_satisfied"],
        "metrics": normalized,
        "thresholds": limits,
    }


def build_good_solution_report(
    rows: Mapping[str, Any], *, thresholds: Mapping[str, float] | None = None
) -> dict[str, Any]:
    """Classify every result-map row and return a machine-readable report."""
    evaluations: list[dict[str, Any]] = []
    for map_name, raw_row in sorted(rows.items()):
        row = raw_row if isinstance(raw_row, dict) else {}
        filename = str(row.get("filename") or map_name)
        result = evaluate_good_solution(
            row,
            source_status=str(row.get("status") or ""),
            thresholds=thresholds,
        )
        evaluations.append({"filename": filename, **result})
    counts = Counter(item["status"] for item in evaluations)
    return {
        "schema_version": SCHEMA_VERSION,
        "statuses": list(STATUSES),
        "thresholds": {**DEFAULT_THRESHOLDS, **(thresholds or {})},
        "summary": {"file_count": len(evaluations), **{name: counts[name] for name in STATUSES}},
        "evaluations": evaluations,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result_map", type=Path, help="conversion_result_map.json to classify")
    parser.add_argument("--output", type=Path, help="write the report in addition to stdout")
    args = parser.parse_args(argv)
    try:
        rows = json.loads(args.result_map.read_text(encoding="utf-8"))
        if not isinstance(rows, dict):
            raise ValueError("result map must be a JSON object")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))
    report = build_good_solution_report(rows)
    serialized = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
