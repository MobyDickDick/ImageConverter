#!/usr/bin/env python3
"""Run the IDO-21 end-to-end holdout acceptance report.

The v1 report ties together the catalog-free holdout rename protocol, the
image+description ablation result, the quality/complexity gate, and the
uncertainty contract.  It uses only anonymized holdout evaluation names in the
conversion rows so the report can be checked for leakage before real withheld
artifacts are substituted.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_holdout_ablation_matrix import build_ablation_matrix
from tools.define_holdout_rename_protocol import DEFAULT_SEED, build_protocol, default_samples
from tools.evaluate_quality_complexity_gate import evaluate_quality_complexity_gate

DEFAULT_OUTPUT = ROOT / "artifacts" / "evaluation" / "end_to_end_holdout_acceptance_v1" / "end_to_end_holdout_acceptance_v1.json"
CATALOG_TOKEN_RE = re.compile(r"\b(?:AC|AR|GE|DLG|SE)\d{3,4}(?:_[0-9A-Z]+)?\b")


def _svg_for_sample(evaluation_name: str, contributions: dict[str, list[str]]) -> str:
    """Build a compact vector-only SVG from source contributions."""
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24">']
    if "circle" in contributions.get("image", []) or "circle" in contributions.get("description", []):
        parts.append('<circle cx="12" cy="12" r="7" fill="none" stroke="black"/>')
    if "line" in contributions.get("image", []) or "line" in contributions.get("description", []):
        parts.append('<line x1="12" y1="4" x2="12" y2="0" stroke="black"/>')
    if "polygon" in contributions.get("image", []) or "polygon" in contributions.get("description", []):
        parts.append('<polygon points="5,19 12,7 19,19" fill="none" stroke="black"/>')
    if "text" in contributions.get("description", []):
        parts.append('<text x="12" y="14" text-anchor="middle" font-size="5">TXT</text>')
    parts.append(f'<!-- evaluation:{evaluation_name} -->')
    parts.append("</svg>")
    return "".join(parts)


def _uncertainty_for_row(row: dict[str, Any], gate_result: dict[str, Any]) -> dict[str, Any]:
    confidence = min(
        float(row["metrics"].get("semantic_score", 0.0)),
        float(row["metrics"].get("structure_score", 0.0)),
        float(row["metrics"].get("combined_score", 0.0)),
    )
    review_required = not gate_result["passed"] or confidence < 0.78
    return {
        "schema_version": "fusion_uncertainty_v1",
        "status": "resolved" if not review_required else "review_required",
        "reasons": [] if not review_required else ["quality_or_confidence_below_acceptance"],
        "confidence": round(confidence, 4),
        "review_required": review_required,
        "targets": [] if not review_required else [row["evaluation_name"]],
    }


def _holdout_original_names(protocol: dict[str, Any]) -> set[str]:
    return {str(sample["original_name"]) for sample in protocol["samples"] if sample["split"] == "holdout"}


def build_end_to_end_holdout_acceptance(*, seed: str = DEFAULT_SEED) -> dict[str, Any]:
    protocol = build_protocol(default_samples(), seed=seed)
    matrix = build_ablation_matrix(protocol)
    holdout_original_names = _holdout_original_names(protocol)
    holdout_rows = [
        row for row in matrix["rows"]
        if row["split"] == "holdout" and row["mode"] == "image_and_description"
    ]

    conversions: list[dict[str, Any]] = []
    for row in holdout_rows:
        svg = _svg_for_sample(row["evaluation_name"], row["source_contributions"])
        gate = evaluate_quality_complexity_gate(row["metrics"], svg)
        uncertainty = _uncertainty_for_row(row, gate)
        conversions.append({
            "evaluation_name": row["evaluation_name"],
            "mode": row["mode"],
            "source_contributions": row["source_contributions"],
            "rename_invariant": str(row["evaluation_name"]).startswith("holdout_"),
            "metrics": row["metrics"],
            "quality_gate": gate,
            "uncertainty": uncertainty,
            "svg_preview": svg,
        })

    serialized_conversions = json.dumps(conversions, ensure_ascii=False)
    leaked_original_names = sorted(name for name in holdout_original_names if name in serialized_conversions)
    leaked_catalog_tokens = sorted(set(CATALOG_TOKEN_RE.findall(serialized_conversions)))
    summary = {
        "holdout_sample_count": len(conversions),
        "rename_invariance_passed": all(item["rename_invariant"] for item in conversions),
        "quality_gate_passed": all(item["quality_gate"]["passed"] for item in conversions),
        "uncertainty_calibration_passed": all(not item["uncertainty"]["review_required"] for item in conversions),
        "no_holdout_name_leakage": not leaked_original_names,
        "no_catalog_token_leakage": not leaked_catalog_tokens,
    }
    summary["accepted"] = all(value for key, value in summary.items() if key != "holdout_sample_count") and bool(conversions)

    return {
        "schema_version": "end_to_end_holdout_acceptance_v1",
        "protocol_schema_version": protocol["schema_version"],
        "ablation_schema_version": matrix["schema_version"],
        "quality_gate_schema_version": "quality_complexity_gate_v1",
        "acceptance_criteria": {
            "uses_anonymized_holdout_names_only": True,
            "requires_image_and_description_mode": True,
            "requires_quality_gate_pass": True,
            "requires_uncertainty_without_review": True,
            "forbids_catalog_tokens_in_runtime_rows": True,
        },
        "summary": summary,
        "leakage": {"holdout_original_names": leaked_original_names, "catalog_tokens": leaked_catalog_tokens},
        "conversions": conversions,
    }


def write_end_to_end_holdout_acceptance(output: Path, *, seed: str = DEFAULT_SEED) -> dict[str, Any]:
    report = build_end_to_end_holdout_acceptance(seed=seed)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seed", default=DEFAULT_SEED)
    args = parser.parse_args()
    report = write_end_to_end_holdout_acceptance(args.output, seed=args.seed)
    print(json.dumps({"output": str(args.output), "summary": report["summary"]}, indent=2))
    return 0 if report["summary"]["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
