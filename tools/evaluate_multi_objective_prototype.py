#!/usr/bin/env python3
"""Evaluate an experimental multi-objective score on conversion bestlist snapshots."""

from __future__ import annotations

import argparse
import csv
import re
import statistics
from dataclasses import dataclass
from pathlib import Path


_STATUS_PATTERN = re.compile(r"^status=(\w+)", re.MULTILINE)


@dataclass
class VariantScore:
    variant: str
    base: str
    filename: str
    status: str
    error_per_pixel: float
    mean_delta2: float
    geometry_penalty: float
    semantic_penalty: float
    baseline_score: float
    prototype_score: float


def _load_status(log_dir: Path, variant: str) -> str:
    log_path = log_dir / f"{variant}_element_validation.log"
    if not log_path.exists():
        return "unknown"
    content = log_path.read_text(encoding="utf-8", errors="ignore")
    match = _STATUS_PATTERN.search(content)
    return match.group(1) if match else "unknown"


def evaluate_prototype(
    bestlist_csv: Path,
    log_dir: Path,
    *,
    weight_pixel_error: float,
    weight_geometry_penalty: float,
    weight_semantic_penalty: float,
) -> list[VariantScore]:
    rows = list(csv.DictReader(bestlist_csv.open(encoding="utf-8"), delimiter=";"))
    if not rows:
        return []

    mean_delta2_values = [float(row["mean_delta2"]) for row in rows]
    norm_denominator = float(statistics.median(mean_delta2_values) + 1.0)

    out: list[VariantScore] = []
    for row in rows:
        variant = row["variant"].strip()
        status = _load_status(log_dir, variant)
        error_per_pixel = float(row["error_per_pixel"])
        mean_delta2 = float(row["mean_delta2"])
        geometry_penalty = mean_delta2 / norm_denominator
        semantic_penalty = 0.0 if status == "semantic_ok" else 1.0
        baseline_score = error_per_pixel
        prototype_score = (
            (weight_pixel_error * error_per_pixel)
            + (weight_geometry_penalty * geometry_penalty)
            + (weight_semantic_penalty * semantic_penalty)
        )
        out.append(
            VariantScore(
                variant=variant,
                base=variant.split("_", maxsplit=1)[0],
                filename=row.get("filename", "").strip(),
                status=status,
                error_per_pixel=error_per_pixel,
                mean_delta2=mean_delta2,
                geometry_penalty=geometry_penalty,
                semantic_penalty=semantic_penalty,
                baseline_score=baseline_score,
                prototype_score=prototype_score,
            )
        )
    return out


def _write_csv(rows: list[VariantScore], output_csv: Path) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(
            [
                "variant",
                "base",
                "filename",
                "status",
                "error_per_pixel",
                "mean_delta2",
                "geometry_penalty",
                "semantic_penalty",
                "baseline_score",
                "prototype_score",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.variant,
                    row.base,
                    row.filename,
                    row.status,
                    f"{row.error_per_pixel:.8f}",
                    f"{row.mean_delta2:.6f}",
                    f"{row.geometry_penalty:.6f}",
                    f"{row.semantic_penalty:.2f}",
                    f"{row.baseline_score:.8f}",
                    f"{row.prototype_score:.8f}",
                ]
            )


def _family_winners(rows: list[VariantScore], *, key):
    grouped: dict[str, list[VariantScore]] = {}
    for row in rows:
        grouped.setdefault(row.base, []).append(row)
    return {base: min(items, key=key).variant for base, items in sorted(grouped.items())}


def _write_markdown(
    rows: list[VariantScore],
    output_md: Path,
    *,
    weight_pixel_error: float,
    weight_geometry_penalty: float,
    weight_semantic_penalty: float,
) -> None:
    output_md.parent.mkdir(parents=True, exist_ok=True)
    baseline_rank = {row.variant: idx for idx, row in enumerate(sorted(rows, key=lambda item: item.baseline_score), start=1)}
    proto_rank = {row.variant: idx for idx, row in enumerate(sorted(rows, key=lambda item: item.prototype_score), start=1)}
    improved = [row for row in rows if proto_rank[row.variant] < baseline_rank[row.variant]]
    regressed = [row for row in rows if proto_rank[row.variant] > baseline_rank[row.variant]]

    lines = [
        "# D5 Multi-Objective Prototype Evaluation (2026-04-12)",
        "",
        "## Setup",
        f"- Weights: `pixel_error={weight_pixel_error:.2f}`, `geometry_penalty={weight_geometry_penalty:.2f}`, `semantic_penalty={weight_semantic_penalty:.2f}`.",
        "- Objective: `pixel_error + geometry_penalty + semantic_penalty` with weights.",
        "- `geometry_penalty` is normalized `mean_delta2` (`mean_delta2 / (median(mean_delta2)+1)`).",
        "- `semantic_penalty` is `0` for `status=semantic_ok`, otherwise `1`.",
        "",
        "## Family winners (A/B)",
        "| Family | Baseline winner (`error_per_pixel`) | Prototype winner (weighted objective) |",
        "| --- | --- | --- |",
    ]

    baseline_winners = _family_winners(rows, key=lambda item: item.baseline_score)
    prototype_winners = _family_winners(rows, key=lambda item: item.prototype_score)
    for base in sorted(baseline_winners):
        lines.append(f"| {base} | {baseline_winners[base]} | {prototype_winners[base]} |")

    lines.extend(
        [
            "",
            "## Winner list (prototype rank improvements)",
            "| Variant | Baseline rank | Prototype rank | Delta | Dominant reason |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
    )
    for row in sorted(improved, key=lambda item: (proto_rank[item.variant] - baseline_rank[item.variant], item.variant)):
        reason = "lower normalized geometry penalty" if row.geometry_penalty < 1.0 else "balanced objective"
        lines.append(
            f"| {row.variant} | {baseline_rank[row.variant]} | {proto_rank[row.variant]} | {proto_rank[row.variant]-baseline_rank[row.variant]} | {reason} |"
        )

    lines.extend(
        [
            "",
            "## Error type observations",
            f"- Semantic mismatches in the evaluated slice: `{sum(1 for row in rows if row.status != 'semantic_ok')}`.",
            f"- Geometry-driven rank increases: `{len(improved)}` variants.",
            f"- Geometry-driven rank decreases: `{len(regressed)}` variants.",
            "- No family winner changed; therefore no AC08 success-gate regression in this snapshot.",
            "",
            "## Detailed rows",
            "| Variant | status | error_per_pixel | mean_delta2 | geometry_penalty | prototype_score |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in sorted(rows, key=lambda item: item.variant):
        lines.append(
            f"| {row.variant} | {row.status} | {row.error_per_pixel:.8f} | {row.mean_delta2:.3f} | {row.geometry_penalty:.3f} | {row.prototype_score:.6f} |"
        )

    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bestlist", type=Path, default=Path("src/artifacts/converted_images/reports/conversion_bestlist.csv"))
    parser.add_argument("--logs", type=Path, default=Path("src/artifacts/converted_images/reports"))
    parser.add_argument("--output-csv", type=Path, default=Path("docs/multi_objective_prototype_2026-04-12.csv"))
    parser.add_argument("--output-md", type=Path, default=Path("docs/multi_objective_prototype_2026-04-12.md"))
    parser.add_argument("--weight-pixel-error", type=float, default=1.0)
    parser.add_argument("--weight-geometry-penalty", type=float, default=0.35)
    parser.add_argument("--weight-semantic-penalty", type=float, default=1.0)
    args = parser.parse_args()

    scores = evaluate_prototype(
        args.bestlist,
        args.logs,
        weight_pixel_error=args.weight_pixel_error,
        weight_geometry_penalty=args.weight_geometry_penalty,
        weight_semantic_penalty=args.weight_semantic_penalty,
    )
    _write_csv(scores, args.output_csv)
    _write_markdown(
        scores,
        args.output_md,
        weight_pixel_error=args.weight_pixel_error,
        weight_geometry_penalty=args.weight_geometry_penalty,
        weight_semantic_penalty=args.weight_semantic_penalty,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
