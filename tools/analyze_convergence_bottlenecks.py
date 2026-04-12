#!/usr/bin/env python3
"""Summarize convergence bottlenecks from element validation logs and bestlist metrics."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIRS = [
    ROOT / "src/artifacts/converted_images/reports",
    ROOT / "artifacts/converted_images/reports",
]

LOG_PATTERN = re.compile(r"^(?P<name>[A-Z]{2}\d{4}(?:_[A-Z0-9]+)?)_element_validation\.log$")
ROUND_ERR_PATTERN = re.compile(r"Runde\s+(?P<round>\d+):\s+Gesamtfehler=(?P<err>[0-9]+(?:\.[0-9]+)?)")


def _safe_float(raw: str) -> float | None:
    text = str(raw).strip().replace(",", ".")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def load_bestlist(path: Path) -> dict[str, dict[str, float | str | None]]:
    if not path.exists():
        return {}
    rows: dict[str, dict[str, float | str | None]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        for row in reader:
            filename = str(row.get("filename", "")).strip()
            if not filename:
                continue
            variant = filename.rsplit(".", 1)[0]
            rows[variant] = {
                "status": str(row.get("status", "")).strip() or None,
                "best_iter": _safe_float(str(row.get("best_iter", ""))),
                "error_per_pixel": _safe_float(str(row.get("error_per_pixel", ""))),
                "mean_delta2": _safe_float(str(row.get("mean_delta2", ""))),
            }
    return rows


def parse_validation_log(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8", errors="replace")
    rounds = [float(m.group("err")) for m in ROUND_ERR_PATTERN.finditer(text)]
    status = None
    for line in text.splitlines():
        if line.startswith("status="):
            status = line.split("=", 1)[1].strip()
            break

    return {
        "status": status,
        "global_skipped": "global-search: übersprungen" in text,
        "width_skipped": "Breiten-Bracketing übersprungen" in text,
        "stagnation": "stagnation_detected" in text,
        "fallback": "switch_to_fallback_search" in text,
        "early_stop": "stopped_due_to_stagnation" in text,
        "color_post": "Farboptimierung in Abschlussphase angewendet" in text,
        "rounds": rounds,
        "round_count": len(rounds),
        "first_err": rounds[0] if rounds else None,
        "best_err": min(rounds) if rounds else None,
        "last_err": rounds[-1] if rounds else None,
    }


def summarize_family(records: dict[str, dict[str, object]], prefix: str) -> dict[str, object]:
    subset = {k: v for k, v in records.items() if k.startswith(prefix)}
    if not subset:
        return {"count": 0}

    def frac(key: str) -> float:
        return sum(1 for data in subset.values() if data.get(key)) / len(subset)

    round_counts = [int(data["round_count"]) for data in subset.values()]
    gains = []
    for data in subset.values():
        first_err = data.get("first_err")
        best_err = data.get("best_err")
        if isinstance(first_err, (int, float)) and isinstance(best_err, (int, float)) and first_err > 0:
            gains.append((first_err - best_err) / first_err)

    return {
        "count": len(subset),
        "global_skip_ratio": frac("global_skipped"),
        "width_skip_ratio": frac("width_skipped"),
        "stagnation_ratio": frac("stagnation"),
        "early_stop_ratio": frac("early_stop"),
        "median_rounds": median(round_counts),
        "max_rounds": max(round_counts),
        "median_relative_gain": median(gains) if gains else None,
        "mean_relative_gain": mean(gains) if gains else None,
    }


def main() -> int:
    all_logs: dict[str, dict[str, object]] = {}
    bestlist_rows: dict[str, dict[str, float | str | None]] = {}

    for report_dir in REPORT_DIRS:
        if not report_dir.exists():
            continue
        bestlist_rows.update(load_bestlist(report_dir / "conversion_bestlist.csv"))
        for path in sorted(report_dir.glob("*_element_validation.log")):
            match = LOG_PATTERN.match(path.name)
            if not match:
                continue
            variant = match.group("name")
            # prefer src/artifacts snapshot if both exist
            if variant in all_logs and "/src/artifacts/" in str(all_logs[variant].get("path", "")):
                continue
            payload = parse_validation_log(path)
            payload["path"] = str(path)
            all_logs[variant] = payload

    family_summaries = {
        "AC08": summarize_family(all_logs, "AC08"),
        "AC0223": summarize_family(all_logs, "AC0223"),
        "AC0023": summarize_family(all_logs, "AC0023"),
        "AC0823": summarize_family(all_logs, "AC0823"),
    }

    worst_ac08 = []
    for variant, row in bestlist_rows.items():
        if not variant.startswith("AC08"):
            continue
        err_pp = row.get("error_per_pixel")
        delta2 = row.get("mean_delta2")
        if not isinstance(err_pp, (int, float)):
            continue
        worst_ac08.append((float(err_pp), float(delta2) if isinstance(delta2, (int, float)) else float("inf"), variant))
    worst_ac08.sort(reverse=True)

    top_worst = []
    for err_pp, delta2, variant in worst_ac08[:10]:
        log = all_logs.get(variant, {})
        top_worst.append(
            {
                "variant": variant,
                "error_per_pixel": err_pp,
                "mean_delta2": delta2,
                "round_count": log.get("round_count"),
                "stagnation": bool(log.get("stagnation")),
                "global_skipped": bool(log.get("global_skipped")),
                "width_skipped": bool(log.get("width_skipped")),
            }
        )

    out = {
        "report_dirs": [str(p) for p in REPORT_DIRS if p.exists()],
        "log_count": len(all_logs),
        "family_summaries": family_summaries,
        "ac08_worst_by_error_per_pixel": top_worst,
    }

    output_path = ROOT / "docs" / "convergence_bottleneck_analysis.json"
    output_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
