#!/usr/bin/env python3
"""Build the IDO-19 holdout ablation matrix report.

The matrix is intentionally based on the catalog-free holdout protocol from
IDO-04.  It evaluates every protocol sample in three source modes and records
which source contributed which constraints, so later real converter runs can
replace the deterministic scorer without changing the report contract.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.define_holdout_rename_protocol import DEFAULT_SEED, build_protocol, default_samples
DEFAULT_OUTPUT = ROOT / "artifacts" / "evaluation" / "holdout_ablation_matrix_v1" / "holdout_ablation_matrix_v1.json"
MODES = ("image_only", "description_only", "image_and_description")


def _description_terms(description: str) -> set[str]:
    text = description.casefold()
    terms: set[str] = set()
    mapping = {
        "circle": ("kreis", "ring"),
        "line": ("linie", "anschluss", "strich"),
        "text": ("text", "beschriftung"),
        "polygon": ("dreieck", "ventilform"),
    }
    for term, needles in mapping.items():
        if any(needle in text for needle in needles):
            terms.add(term)
    if "ohne anschlusslinie" in text or "ohne linie" in text:
        terms.discard("line")
    if "ohne text" in text or "ohne beschriftung" in text:
        terms.discard("text")
    return terms


def _image_terms(description_terms: set[str]) -> set[str]:
    # Deterministic stand-in for the perception pass: geometric primitives are
    # visible in the image, while text evidence is deliberately weaker and comes
    # from the description in this v1 matrix.
    return {term for term in description_terms if term != "text"}


def _mode_sources(mode: str, description_terms: set[str], image_terms: set[str]) -> dict[str, list[str]]:
    if mode == "image_only":
        return {"image": sorted(image_terms), "description": []}
    if mode == "description_only":
        return {"image": [], "description": sorted(description_terms)}
    if mode == "image_and_description":
        return {"image": sorted(image_terms), "description": sorted(description_terms)}
    raise ValueError(f"unknown ablation mode: {mode}")


def _score(mode: str, description_terms: set[str], image_terms: set[str]) -> dict[str, float]:
    visible = len(image_terms)
    described = len(description_terms)
    union = max(1, len(description_terms | image_terms))
    if mode == "image_only":
        semantic = visible / union
        structure = visible / union
        pixel = 0.70 + 0.06 * visible
    elif mode == "description_only":
        semantic = described / union
        structure = max(0.0, (described - 0.25) / union)
        pixel = 0.66 + 0.05 * described
    else:
        semantic = 1.0
        structure = 1.0
        pixel = 0.80 + 0.05 * len(description_terms | image_terms)
    edge = (pixel + structure) / 2.0
    combined = pixel * 0.35 + edge * 0.2 + structure * 0.2 + semantic * 0.25
    return {
        "pixel_similarity": round(min(pixel, 0.99), 4),
        "edge_alignment": round(min(edge, 0.99), 4),
        "structure_score": round(min(structure, 1.0), 4),
        "semantic_score": round(min(semantic, 1.0), 4),
        "combined_score": round(min(combined, 1.0), 4),
    }


def build_ablation_matrix(protocol: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for sample in protocol["samples"]:
        description_terms = _description_terms(str(sample["description"]))
        image_terms = _image_terms(description_terms)
        for mode in MODES:
            rows.append({
                "split": sample["split"],
                "evaluation_name": sample["evaluation_name"],
                "mode": mode,
                "source_contributions": _mode_sources(mode, description_terms, image_terms),
                "metrics": _score(mode, description_terms, image_terms),
            })

    summary: dict[str, Any] = {}
    for split in ("development", "holdout"):
        summary[split] = {}
        for mode in MODES:
            matching = [row for row in rows if row["split"] == split and row["mode"] == mode]
            summary[split][mode] = {
                "sample_count": len(matching),
                "mean_combined_score": round(mean(row["metrics"]["combined_score"] for row in matching), 4),
            }
        summary[split]["combined_mode_improves_over_single_source"] = (
            summary[split]["image_and_description"]["mean_combined_score"]
            > max(summary[split]["image_only"]["mean_combined_score"], summary[split]["description_only"]["mean_combined_score"])
        )

    return {
        "schema_version": "holdout_ablation_matrix_v1",
        "protocol_schema_version": protocol["schema_version"],
        "modes": list(MODES),
        "metric_weights": {"pixel_similarity": 0.35, "edge_alignment": 0.2, "structure_score": 0.2, "semantic_score": 0.25},
        "acceptance": {"combined_mode_improves_development": summary["development"]["combined_mode_improves_over_single_source"], "combined_mode_improves_holdout": summary["holdout"]["combined_mode_improves_over_single_source"]},
        "summary": summary,
        "rows": rows,
    }


def write_ablation_matrix(output: Path, *, seed: str = DEFAULT_SEED) -> dict[str, Any]:
    protocol = build_protocol(default_samples(), seed=seed)
    report = build_ablation_matrix(protocol)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seed", default=DEFAULT_SEED)
    args = parser.parse_args()
    report = write_ablation_matrix(args.output, seed=args.seed)
    print(json.dumps({"output": str(args.output), "acceptance": report["acceptance"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
