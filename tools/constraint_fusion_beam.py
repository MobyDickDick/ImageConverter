#!/usr/bin/env python3
"""Fuse description constraints and perception evidence into a small IR beam.

The module deliberately has no catalogue or filename knowledge.  Its inputs are
the two intermediate products derived from the permitted runtime sources: hard
description constraints and image-perception candidates.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "constraint_fusion_beam_v1"
_KIND_ALIASES = {
    "circlebackground": "circle",
    "ring": "circle",
    "rectborder": "rectangle",
    "textglyph": "text",
    "text_glyph": "text",
    "text_area": "text",
    "horizontalrule": "line",
    "horizontal_rule": "line",
    "vertical_line": "line",
    "orthogonalpolyline": "line",
    "polygonpath": "polygon",
    "path": "polygon",
}


def _kind(value: object) -> str:
    normalized = str(value or "").strip().casefold().replace("-", "_")
    return _KIND_ALIASES.get(normalized, normalized)


def _finite_score(value: object, default: float) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def _candidate_dict(candidate: object) -> dict[str, Any]:
    if hasattr(candidate, "to_dict"):
        candidate = candidate.to_dict()
    if not isinstance(candidate, dict):
        raise ValueError("perception candidates must be objects")
    return candidate


def _stable_candidate_id(candidate: dict[str, Any]) -> str:
    """Return a name-independent evidence ID."""
    evidence = {
        key: candidate.get(key)
        for key in ("kind", "bbox", "center", "geometry", "confidence")
    }
    digest = hashlib.sha256(
        json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:12]
    return f"candidate-{digest}"


def _constraint_id(constraint: dict[str, Any], index: int) -> str:
    return str(constraint.get("id") or f"constraint-{index + 1}")


def _expected_kind(constraint: dict[str, Any]) -> str:
    return _kind(constraint.get("primitive_type", constraint.get("kind")))


def _position(candidate: dict[str, Any]) -> str | None:
    geometry = candidate.get("geometry")
    for container in (candidate, geometry if isinstance(geometry, dict) else {}):
        for key in ("relative_position", "position", "side"):
            if container.get(key):
                return str(container[key]).casefold()
    return None


def _direction(candidate: dict[str, Any]) -> str | None:
    geometry = candidate.get("geometry")
    for container in (candidate, geometry if isinstance(geometry, dict) else {}):
        for key in ("direction", "orientation", "connector_direction"):
            if container.get(key):
                return str(container[key]).casefold()
    return None


def _compatibility_reasons(
    constraint: dict[str, Any], candidate: dict[str, Any]
) -> list[str]:
    reasons: list[str] = []
    expected, actual = _expected_kind(constraint), _kind(candidate.get("kind"))
    if expected != actual:
        reasons.append(f"primitive_type:{actual or 'missing'}!={expected or 'missing'}")
    expected_position = constraint.get("relative_position", constraint.get("position"))
    if expected_position and _position(candidate) != str(expected_position).casefold():
        reasons.append(
            f"relative_position:{_position(candidate) or 'missing'}!={str(expected_position).casefold()}"
        )
    expected_direction = constraint.get(
        "connector_direction", constraint.get("direction")
    )
    if expected_direction and _direction(candidate) != str(expected_direction).casefold():
        reasons.append(
            f"connector_direction:{_direction(candidate) or 'missing'}!={str(expected_direction).casefold()}"
        )
    return reasons


def _relation_reasons(
    relations: Iterable[dict[str, Any]], assignment: dict[str, dict[str, Any]]
) -> list[str]:
    reasons: list[str] = []
    for relation in relations:
        source = assignment.get(str(relation.get("source")))
        target = assignment.get(str(relation.get("target")))
        if source is None or target is None:
            reasons.append(f"relation:{relation.get('id', 'unnamed')}:missing_endpoint")
            continue
        expected = relation.get("direction", relation.get("relative_position"))
        if expected and _position(source) != str(expected).casefold():
            reasons.append(
                f"relation:{relation.get('id', 'unnamed')}:direction_mismatch"
            )
    return reasons


def build_constraint_fusion_beam(
    description_constraints: dict[str, Any],
    perception_candidates: list[object],
    *,
    beam_width: int = 3,
) -> dict[str, Any]:
    """Build a deterministic, semantics-first beam of Geometry-IR hypotheses.

    ``pixel_error`` is accepted as candidate telemetry, but it is only the last
    tie-breaker after all hard constraints and confidence.  Consequently a
    pixel-closer primitive of the wrong type, location or direction cannot win.
    """
    if beam_width < 3:
        raise ValueError("beam_width must retain at least three hypotheses")
    raw_constraints = description_constraints.get("elements", [])
    if not isinstance(raw_constraints, list) or not raw_constraints:
        raise ValueError("description constraints require a non-empty elements list")
    constraints = [item for item in raw_constraints if isinstance(item, dict)]
    if len(constraints) != len(raw_constraints):
        raise ValueError("description constraint elements must be objects")
    candidates = [_candidate_dict(item) for item in perception_candidates]
    indexed = [(_stable_candidate_id(item), item) for item in candidates]
    indexed.sort(key=lambda item: item[0])

    options: list[list[tuple[str, dict[str, Any]]]] = []
    rejections: list[dict[str, Any]] = []
    for index, constraint in enumerate(constraints):
        constraint_id = _constraint_id(constraint, index)
        matches: list[tuple[str, dict[str, Any]]] = []
        for candidate_id, candidate in indexed:
            reasons = _compatibility_reasons(constraint, candidate)
            if reasons:
                rejections.append(
                    {
                        "constraint_id": constraint_id,
                        "candidate_id": candidate_id,
                        "reasons": reasons,
                    }
                )
            else:
                matches.append((candidate_id, candidate))
        options.append(matches)

    hypotheses: list[dict[str, Any]] = []
    rejected_hypotheses: list[dict[str, Any]] = []
    if all(options):
        for combination in itertools.product(*options):
            ids = [item[0] for item in combination]
            if len(ids) != len(set(ids)):
                rejected_hypotheses.append(
                    {"candidate_ids": ids, "reasons": ["candidate_reused"]}
                )
                continue
            assignment = {
                _constraint_id(constraint, index): combination[index][1]
                for index, constraint in enumerate(constraints)
            }
            relation_reasons = _relation_reasons(
                [item for item in description_constraints.get("relations", []) if isinstance(item, dict)],
                assignment,
            )
            if relation_reasons:
                rejected_hypotheses.append(
                    {"candidate_ids": ids, "reasons": relation_reasons}
                )
                continue
            confidence = sum(
                max(0.0, min(1.0, _finite_score(item[1].get("confidence"), 0.0)))
                for item in combination
            ) / len(combination)
            pixel_error = sum(
                max(0.0, _finite_score(item[1].get("pixel_error"), 1.0))
                for item in combination
            ) / len(combination)
            signature = json.dumps(ids, separators=(",", ":"))
            hypotheses.append(
                {
                    "hypothesis_id": "hypothesis-"
                    + hashlib.sha256(signature.encode()).hexdigest()[:12],
                    "rank": 0,
                    "hard_constraints_satisfied": True,
                    "semantic_score": 1.0,
                    "confidence": round(confidence, 6),
                    "pixel_error": round(pixel_error, 6),
                    "assignments": [
                        {
                            "constraint_id": _constraint_id(constraints[i], i),
                            "candidate_id": ids[i],
                            "primitive_type": _expected_kind(constraints[i]),
                        }
                        for i in range(len(constraints))
                    ],
                    "geometry_ir": [item[1].get("geometry", {}) for item in combination],
                }
            )
    hypotheses.sort(
        key=lambda item: (-item["semantic_score"], -item["confidence"], item["pixel_error"], item["hypothesis_id"])
    )
    hypotheses = hypotheses[:beam_width]
    for rank, hypothesis in enumerate(hypotheses, start=1):
        hypothesis["rank"] = rank

    missing = [
        _constraint_id(constraint, index)
        for index, (constraint, matches) in enumerate(zip(constraints, options))
        if not matches
    ]
    status = "resolved" if hypotheses else "semantic_conflict"
    conflict_reasons = (
        [f"missing_compatible_evidence:{item}" for item in missing]
        if missing
        else ([] if hypotheses else ["no_hypothesis_satisfies_hard_relations"])
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "beam_width": beam_width,
        "ranking_policy": ["hard_constraints", "semantic_score", "confidence", "pixel_error"],
        "hypotheses": hypotheses,
        "selected_hypothesis_id": hypotheses[0]["hypothesis_id"] if hypotheses else None,
        "conflicts": conflict_reasons,
        "rejected_candidates": sorted(
            rejections, key=lambda item: (item["constraint_id"], item["candidate_id"])
        ),
        "rejected_hypotheses": rejected_hypotheses,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON with constraints and candidates")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--beam-width", type=int, default=3)
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        report = build_constraint_fusion_beam(
            payload["description_constraints"],
            payload["perception_candidates"],
            beam_width=args.beam_width,
        )
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    serialized = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 0 if report["status"] == "resolved" else 23


if __name__ == "__main__":
    raise SystemExit(main())
