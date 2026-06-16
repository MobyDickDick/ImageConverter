#!/usr/bin/env python3
"""Define the IDO-04 holdout/rename evaluation protocol.

The protocol is intentionally data-only: it records how development and strict
holdout samples are separated, how holdout filenames are anonymized for an
actual evaluation run, and which metric families every report must publish.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "artifacts" / "evaluation" / "holdout_rename_protocol_v1" / "holdout_rename_protocol_v1.json"
DEFAULT_SEED = "ido-04-holdout-rename-v1"
METRIC_FAMILIES = ("pixel", "edge", "structure", "semantic")


@dataclass(frozen=True)
class EvaluationSample:
    original_name: str
    description: str
    split: str

    def to_record(self, *, seed: str) -> dict[str, object]:
        record: dict[str, object] = {
            "original_name": self.original_name,
            "description": self.description,
            "split": self.split,
        }
        if self.split == "holdout":
            record["evaluation_name"] = anonymized_holdout_name(self.original_name, seed=seed)
            record["rename_required"] = True
        else:
            record["evaluation_name"] = self.original_name
            record["rename_required"] = False
        return record


def anonymized_holdout_name(original_name: str, *, seed: str = DEFAULT_SEED) -> str:
    """Return a stable, catalog-free evaluation filename for a holdout sample."""
    suffix = Path(original_name).suffix or ".png"
    digest = hashlib.sha256(f"{seed}\0{original_name}".encode("utf-8")).hexdigest()[:16]
    return f"holdout_{digest}{suffix.lower()}"


def build_metric_contract() -> dict[str, dict[str, object]]:
    return {
        "pixel": {
            "required": True,
            "metrics": ["mean_delta2", "error_per_pixel", "non_background_iou"],
            "reported_per_split": ["development", "holdout"],
        },
        "edge": {
            "required": True,
            "metrics": ["edge_iou", "chamfer_distance_px", "edge_recall"],
            "reported_per_split": ["development", "holdout"],
        },
        "structure": {
            "required": True,
            "metrics": ["primitive_count_delta", "bbox_iou", "path_complexity_ratio"],
            "reported_per_split": ["development", "holdout"],
        },
        "semantic": {
            "required": True,
            "metrics": ["constraint_precision", "constraint_recall", "semantic_status"],
            "reported_per_split": ["development", "holdout"],
        },
    }


def default_samples() -> list[EvaluationSample]:
    return [
        EvaluationSample(
            original_name="development_circle_badge.png",
            description="Kreis mit zentriertem Text und ohne Anschlusslinie",
            split="development",
        ),
        EvaluationSample(
            original_name="development_left_connector.png",
            description="Kreis mit linker horizontaler Anschlusslinie",
            split="development",
        ),
        EvaluationSample(
            original_name="strict_holdout_ring_top_stem.png",
            description="Ring mit oberem senkrechtem Anschluss und kurzer Beschriftung",
            split="holdout",
        ),
        EvaluationSample(
            original_name="strict_holdout_plain_valve.png",
            description="Einfache Ventilform aus Kreis, Linie und Dreieck ohne Text",
            split="holdout",
        ),
    ]


def build_protocol(samples: Iterable[EvaluationSample], *, seed: str = DEFAULT_SEED) -> dict[str, object]:
    sample_records = [sample.to_record(seed=seed) for sample in samples]
    split_counts = {
        split: sum(1 for sample in sample_records if sample["split"] == split)
        for split in ("development", "holdout")
    }
    return {
        "schema_version": "holdout_rename_protocol_v1",
        "seed": seed,
        "split_policy": {
            "development": "Samples available for implementation and threshold tuning.",
            "holdout": "Strictly withheld samples; evaluation must use anonymized filenames only.",
            "forbidden_leakage": [
                "holdout original filenames in runtime code",
                "holdout geometry copied to configuration",
                "threshold tuning on holdout results",
            ],
        },
        "rename_policy": {
            "holdout_renamed_before_conversion": True,
            "rename_algorithm": "sha256(seed + NUL + original_name) first 16 hex characters",
            "development_renamed": False,
        },
        "metric_contract": build_metric_contract(),
        "required_split_reports": {
            split: {family: {"required": True} for family in METRIC_FAMILIES}
            for split in ("development", "holdout")
        },
        "split_counts": split_counts,
        "samples": sample_records,
    }


def write_protocol(output: Path, *, seed: str = DEFAULT_SEED) -> dict[str, object]:
    protocol = build_protocol(default_samples(), seed=seed)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(protocol, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return protocol


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seed", default=DEFAULT_SEED)
    args = parser.parse_args()
    protocol = write_protocol(args.output, seed=args.seed)
    print(json.dumps({"output": str(args.output), "split_counts": protocol["split_counts"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
