#!/usr/bin/env python3
"""Deterministic two-phase multi-objective optimization for Geometry-IR.

The optimizer consumes the semantically valid beam produced by ZG7.3.  It
first selects a discrete topology and z-order, then adjusts numeric geometry,
stroke, colour and gradient parameters without ever accepting a hard-constraint
regression.  A target record is deliberately explicit: in the real pipeline it
is produced by image perception, while tests can use small synthetic records.
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import math
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "multi_objective_optimization_report_v1"
WEIGHTS = {"pixel": 0.40, "edge": 0.25, "structure": 0.20, "semantic": 0.15}
_GEOMETRY_KEYS = {
    "x",
    "y",
    "cx",
    "cy",
    "x1",
    "y1",
    "x2",
    "y2",
    "width",
    "height",
    "r",
    "rx",
    "ry",
}
_EDGE_KEYS = {"stroke_width", "stroke", "offset"}


def _finite(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _elements(geometry_ir: object) -> list[dict[str, Any]]:
    if isinstance(geometry_ir, dict):
        geometry_ir = geometry_ir.get("elements", [])
    if not isinstance(geometry_ir, list) or not all(
        isinstance(item, dict) for item in geometry_ir
    ):
        raise ValueError("geometry_ir must be a list of element objects")
    return geometry_ir


def _hard_violations(
    elements: list[dict[str, Any]], constraints: dict[str, Any]
) -> list[str]:
    violations: list[str] = []
    required = constraints.get("required_kinds", [])
    actual = [
        str(item.get("kind", item.get("primitive_type", ""))).casefold()
        for item in elements
    ]
    for kind in required:
        if str(kind).casefold() not in actual:
            violations.append(f"missing_required_kind:{str(kind).casefold()}")
    expected_order = [str(value) for value in constraints.get("z_order", [])]
    if expected_order:
        actual_order = [
            str(item.get("id", index)) for index, item in enumerate(elements)
        ]
        if actual_order != expected_order:
            violations.append("z_order_mismatch")
    for key, expected in sorted(constraints.get("locked_values", {}).items()):
        try:
            index_text, field = key.split(".", 1)
            actual_value = elements[int(index_text)].get(field)
        except (ValueError, IndexError):
            actual_value = None
        if actual_value != expected:
            violations.append(f"locked_value_mismatch:{key}")
    return violations


def _losses(
    elements: list[dict[str, Any]],
    target: list[dict[str, Any]],
    constraints: dict[str, Any],
) -> dict[str, float]:
    numeric: list[float] = []
    edges: list[float] = []
    structure_mismatches = abs(len(elements) - len(target))
    comparisons = max(len(elements), len(target), 1)
    for index in range(min(len(elements), len(target))):
        current, wanted = elements[index], target[index]
        if current.get("kind", current.get("primitive_type")) != wanted.get(
            "kind", wanted.get("primitive_type")
        ):
            structure_mismatches += 1
        for key, expected_value in wanted.items():
            expected = _finite(expected_value)
            actual = _finite(current.get(key))
            if expected is None or actual is None:
                continue
            scale = max(abs(expected), 1.0)
            delta = min(abs(actual - expected) / scale, 1.0)
            numeric.append(delta)
            if key in _GEOMETRY_KEYS or key in _EDGE_KEYS:
                edges.append(delta)
    semantic = 1.0 if _hard_violations(elements, constraints) else 0.0
    values = {
        "pixel": sum(numeric) / len(numeric) if numeric else 0.0,
        "edge": sum(edges) / len(edges) if edges else 0.0,
        "structure": min(structure_mismatches / comparisons, 1.0),
        "semantic": semantic,
    }
    values["total"] = sum(values[name] * WEIGHTS[name] for name in WEIGHTS)
    return {name: round(value, 12) for name, value in values.items()}


def optimize_geometry_ir(
    fusion_record: dict[str, Any],
    target_geometry_ir: object,
    *,
    hard_constraints: dict[str, Any] | None = None,
    budget: int = 100,
    stagnation_limit: int = 20,
    trust_region: float = 8.0,
) -> dict[str, Any]:
    """Optimize a valid ZG7.3 beam and return a complete iteration report."""
    if budget < 1 or stagnation_limit < 1 or trust_region <= 0:
        raise ValueError("budget, stagnation_limit and trust_region must be positive")
    constraints = hard_constraints or {}
    target = _elements(target_geometry_ir)
    hypotheses = fusion_record.get("hypotheses", [])
    if fusion_record.get("status") != "resolved" or not hypotheses:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "not_reachable",
            "reason": "semantic_conflict",
            "iterations": [],
            "accepted_iterations": 0,
            "initial_loss": None,
            "final_loss": None,
        }

    valid: list[tuple[dict[str, Any], list[dict[str, Any]], dict[str, float]]] = []
    rejected: list[dict[str, Any]] = []
    for hypothesis in hypotheses:
        geometry = copy.deepcopy(_elements(hypothesis.get("geometry_ir", [])))
        violations = _hard_violations(geometry, constraints)
        if not hypothesis.get("hard_constraints_satisfied", False) or violations:
            rejected.append(
                {
                    "hypothesis_id": hypothesis.get("hypothesis_id"),
                    "reasons": violations or ["beam_hard_constraint_failed"],
                }
            )
            continue
        valid.append((hypothesis, geometry, _losses(geometry, target, constraints)))
    if not valid:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "not_reachable",
            "reason": "semantic_conflict",
            "iterations": [],
            "accepted_iterations": 0,
            "initial_loss": None,
            "final_loss": None,
            "rejected_hypotheses": rejected,
        }
    valid.sort(key=lambda row: (row[2]["total"], str(row[0].get("hypothesis_id", ""))))
    selected, current, initial = valid[0]
    current_loss = initial
    iterations: list[dict[str, Any]] = [
        {
            "iteration": 0,
            "phase": "discrete",
            "accepted": True,
            "change": f"select:{selected.get('hypothesis_id')}",
            "losses": initial,
            "hard_violations": [],
        }
    ]
    attempts = 0
    stagnant = 0
    termination = "stagnation"
    stages = (
        ("coarse", trust_region),
        ("fine", trust_region / 4.0),
        ("fine", trust_region / 16.0),
    )
    for stage, step in stages:
        for index, wanted in enumerate(target[: len(current)]):
            for key in sorted(wanted):
                expected, actual = _finite(wanted[key]), _finite(
                    current[index].get(key)
                )
                if expected is None or actual is None or actual == expected:
                    continue
                if attempts >= budget:
                    termination = "budget_exceeded"
                    break
                attempts += 1
                proposal = copy.deepcopy(current)
                delta = max(-step, min(step, expected - actual))
                proposal[index][key] = round(actual + delta, 12)
                violations = _hard_violations(proposal, constraints)
                proposed_loss = _losses(proposal, target, constraints)
                accepted = (
                    not violations
                    and proposed_loss["total"] < current_loss["total"] - 1e-12
                )
                if accepted:
                    current, current_loss, stagnant = proposal, proposed_loss, 0
                else:
                    stagnant += 1
                iterations.append(
                    {
                        "iteration": attempts,
                        "phase": f"continuous_{stage}",
                        "accepted": accepted,
                        "change": f"element[{index}].{key}:{actual}->{proposal[index][key]}",
                        "losses": proposed_loss,
                        "hard_violations": violations,
                    }
                )
                if stagnant >= stagnation_limit:
                    termination = "stagnation"
                    break
            if attempts >= budget or stagnant >= stagnation_limit:
                break
        if attempts >= budget or stagnant >= stagnation_limit:
            break
    else:
        termination = "converged" if current_loss["total"] <= 1e-12 else "stagnation"
    status = "optimized" if current_loss["total"] < initial["total"] else "unchanged"
    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "termination_reason": termination,
        "budget": budget,
        "iterations_used": attempts,
        "accepted_iterations": sum(row["accepted"] for row in iterations[1:]),
        "selected_hypothesis_id": selected.get("hypothesis_id"),
        "weights": WEIGHTS,
        "initial_loss": initial,
        "final_loss": current_loss,
        "geometry_ir": current,
        "iterations": iterations,
        "rejected_hypotheses": rejected,
    }


def _write_csv(path: Path, iterations: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "iteration",
                "phase",
                "accepted",
                "change",
                "pixel_loss",
                "edge_loss",
                "structure_loss",
                "semantic_loss",
                "total_loss",
                "hard_violations",
            ],
        )
        writer.writeheader()
        for row in iterations:
            writer.writerow(
                {
                    "iteration": row["iteration"],
                    "phase": row["phase"],
                    "accepted": str(row["accepted"]).lower(),
                    "change": row["change"],
                    **{
                        f"{name}_loss": row["losses"][name]
                        for name in (*WEIGHTS, "total")
                    },
                    "hard_violations": "|".join(row["hard_violations"]),
                }
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input", type=Path, help="JSON with fusion_record and target_geometry_ir"
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--convergence-csv", type=Path)
    parser.add_argument("--budget", type=int, default=100)
    parser.add_argument("--stagnation-limit", type=int, default=20)
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        report = optimize_geometry_ir(
            payload["fusion_record"],
            payload["target_geometry_ir"],
            hard_constraints=payload.get("hard_constraints"),
            budget=args.budget,
            stagnation_limit=args.stagnation_limit,
        )
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    serialized = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    if args.convergence_csv:
        _write_csv(args.convergence_csv, report["iterations"])
    print(serialized, end="")
    return (
        23
        if report.get("reason") == "semantic_conflict"
        else 21 if report.get("termination_reason") == "budget_exceeded" else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
