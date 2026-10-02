#!/usr/bin/env python3
"""Build the AP3 quality queue from one completed conversion run."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.check_report_consistency import evaluate_report_consistency


SCHEMA_VERSION = "conversion_quality_queue_v1"
SEMANTIC_FAILURE_STATUSES = {
    "conversion_failed",
    "needs_review",
    "semantic_mismatch",
    "semantic_rejected",
}


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _family(filename: str) -> str:
    stem = Path(filename).stem.upper()
    match = re.match(r"([A-Z]+)(\d{2})", stem)
    return "".join(match.groups()) if match else stem.split("_", 1)[0]


def _artifact(path: Path) -> dict[str, Any]:
    return {"path": str(path), "exists": path.is_file()}


def _hypothesis(entry: dict[str, Any]) -> str:
    reason = str(entry.get("diff_error_distribution_reason", "")).strip()
    distribution = str(entry.get("diff_error_distribution_status", "")).strip()
    if reason:
        return f"structured_diff:{reason}"
    if distribution:
        return f"diff_distribution:{distribution}"
    return "pixel_error_requires_visual_triage"


def build_quality_queue(
    reports_dir: str | Path,
    *,
    limit: int = 5,
    input_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Return a queue only when AP0/AP4 prove a coherent, completed run."""
    root = Path(reports_dir)
    source_root = Path(input_dir) if input_dir is not None else root.parent.parent / "images_to_convert"
    consistency = evaluate_report_consistency(root)
    if consistency["status"] != "complete":
        raise ValueError(f"quality queue requires a complete run (got {consistency['status']})")
    result_map = json.loads((root / "conversion_result_map.json").read_text(encoding="utf-8"))

    ranked: list[tuple[float, str, dict[str, Any]]] = []
    excluded: list[dict[str, str]] = []
    for map_name, raw_entry in result_map.items():
        if not isinstance(raw_entry, dict):
            excluded.append({"filename": str(map_name), "reason": "invalid_result_entry"})
            continue
        filename = str(raw_entry.get("filename") or map_name)
        status = str(raw_entry.get("status", "")).strip().lower()
        if status in SEMANTIC_FAILURE_STATUSES or "semantic" in status and status != "semantic_ok":
            excluded.append({"filename": filename, "reason": f"semantic_status:{status}"})
            continue
        mean_delta2 = _number(raw_entry.get("mean_delta2"))
        if mean_delta2 is None:
            excluded.append({"filename": filename, "reason": "missing_mean_delta2"})
            continue
        ranked.append((mean_delta2, filename, raw_entry))

    ranked.sort(key=lambda item: (-item[0], item[1]))
    selected: list[tuple[float, str, dict[str, Any]]] = []
    family_counts: dict[str, int] = {}
    for item in ranked:
        family = _family(item[1])
        if family_counts.get(family, 0) >= 2:
            continue
        selected.append(item)
        family_counts[family] = family_counts.get(family, 0) + 1
        if len(selected) == limit:
            break

    candidates = []
    for position, (mean_delta2, filename, entry) in enumerate(selected, 1):
        width = _number(entry.get("w"))
        height = _number(entry.get("h"))
        candidates.append(
            {
                "rank": position,
                "filename": filename,
                "family": _family(filename),
                "metrics": {
                    "mean_delta2": mean_delta2,
                    "spatial_quality_score": _number(entry.get("spatial_quality_score")),
                    "error_per_pixel": _number(entry.get("error_per_pixel")),
                    "image_area": width * height if width is not None and height is not None else None,
                    "diff_error_distribution_status": entry.get("diff_error_distribution_status"),
                },
                "artifacts": {
                    "source_image": _artifact(source_root / filename),
                    "svg": _artifact(root.parent / "converted_svgs" / f"{Path(filename).stem}.svg"),
                    "diff": _artifact(root.parent / "diff_pngs" / f"{Path(filename).stem}_diff.png"),
                },
                "generation_path": str(entry.get("generation_path") or entry.get("params", {}).get("mode", "unknown")),
                "dominant_residual_hypothesis": _hypothesis(entry),
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": consistency["run_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_report": str(root / "conversion_result_map.json"),
        "input_count": consistency["input_count"],
        "processed_count": consistency["processed_count"],
        "candidate_count": len(candidates),
        "ranking": "mean_delta2_desc_with_max_two_candidates_per_family",
        "candidates": candidates,
        "excluded_results": excluded,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports_dir", nargs="?", default="artifacts/converted_images/reports")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--input-dir", type=Path, help="Source-image directory (defaults beside the output tree).")
    parser.add_argument("--limit", type=int, default=5, choices=range(1, 6), metavar="1..5")
    args = parser.parse_args(argv)
    try:
        report = build_quality_queue(args.reports_dir, limit=args.limit, input_dir=args.input_dir)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    serialized = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
