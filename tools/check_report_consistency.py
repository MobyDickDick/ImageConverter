#!/usr/bin/env python3
"""Validate that conversion reports describe one coherent catalog run."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "report_consistency_gate_v1"
EXIT_FAILURE_STATUSES = {"stale/mixed-run", "invalid"}


def _load_json(path: Path, errors: list[str], *, required: bool = False) -> dict[str, Any] | None:
    if not path.is_file():
        if required:
            errors.append(f"missing_report:{path.name}")
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid_json:{path.name}:{exc}")
        return None
    if not isinstance(payload, dict):
        errors.append(f"invalid_object:{path.name}")
        return None
    return payload


def _load_key_values(path: Path, errors: list[str]) -> dict[str, str] | None:
    if not path.is_file():
        return None
    values: dict[str, str] = {}
    try:
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            if not raw_line.strip():
                continue
            if "=" not in raw_line:
                errors.append(f"invalid_summary_line:{path.name}")
                continue
            key, value = raw_line.split("=", 1)
            if key in values:
                errors.append(f"duplicate_summary_key:{path.name}:{key}")
            values[key] = value
    except OSError as exc:
        errors.append(f"unreadable_report:{path.name}:{exc}")
        return None
    return values


def _non_negative_int(value: Any, field: str, errors: list[str]) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        errors.append(f"invalid_counter:{field}")
        return None
    return value


def _csv_rows(path: Path, errors: list[str]) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle, delimiter=";"))
    except (OSError, csv.Error) as exc:
        errors.append(f"invalid_csv:{path.name}:{exc}")
        return []


def evaluate_report_consistency(reports_dir: str | Path) -> dict[str, Any]:
    """Return a machine-readable consistency decision for ``reports_dir``."""
    root = Path(reports_dir)
    errors: list[str] = []
    stale_reasons: list[str] = []
    warnings: list[str] = []
    checkpoint_path = root / "conversion_checkpoint.json"
    result_map_path = root / "conversion_result_map.json"
    checked_paths = (
        checkpoint_path,
        result_map_path,
        root / "conversion_run_manifest.json",
        root / "chain_phase_telemetry_summary.txt",
        root / "chain_phase_telemetry.csv",
        root / "batch_failure_summary.csv",
    )
    checkpoint = _load_json(checkpoint_path, errors, required=True)
    result_map = _load_json(result_map_path, errors, required=True)
    manifest = _load_json(checked_paths[2], errors)
    chain_summary = _load_key_values(checked_paths[3], errors)

    result_count = len(result_map) if result_map is not None else 0
    run_id = str((checkpoint or {}).get("run_id", "")).strip()
    stage = str((checkpoint or {}).get("stage", "")).strip()
    input_count = 0

    if checkpoint is not None:
        if checkpoint.get("schema_version") != "conversion_checkpoint_v1":
            errors.append("unsupported_schema:conversion_checkpoint.json")
        checkpoint_count = _non_negative_int(
            checkpoint.get("processed_result_count"), "checkpoint.processed_result_count", errors
        )
        if checkpoint_count is not None and checkpoint_count != result_count:
            stale_reasons.append("checkpoint_result_map_count_mismatch")
        if not run_id:
            warnings.append("checkpoint_has_no_run_id")

    if manifest is not None:
        if manifest.get("schema_version") != "conversion_run_manifest_v1":
            errors.append("unsupported_schema:conversion_run_manifest.json")
        manifest_run_id = str(manifest.get("run_id", "")).strip()
        if run_id and manifest_run_id != run_id:
            stale_reasons.append("manifest_run_id_mismatch")
        manifest_count = _non_negative_int(
            manifest.get("processed_result_count"), "manifest.processed_result_count", errors
        )
        parsed_input_count = _non_negative_int(manifest.get("input_count"), "manifest.input_count", errors)
        if parsed_input_count is not None:
            input_count = parsed_input_count
        if manifest_count is not None and manifest_count != result_count:
            stale_reasons.append("manifest_result_map_count_mismatch")
        for field in ("successful_count", "failure_count", "domain_failure_count", "technical_failure_count", "timeout_count"):
            _non_negative_int(manifest.get(field), f"manifest.{field}", errors)
    elif stage == "complete":
        errors.append("complete_checkpoint_without_manifest")

    if chain_summary is not None:
        try:
            chain_count = int(chain_summary.get("conversion_count", ""))
        except ValueError:
            errors.append("invalid_counter:chain_summary.conversion_count")
        else:
            if chain_count < 0:
                errors.append("invalid_counter:chain_summary.conversion_count")
            elif result_count and chain_count == 0:
                stale_reasons.append("empty_chain_summary_for_nonempty_result_map")
            elif chain_count > result_count:
                stale_reasons.append("chain_summary_exceeds_result_map")

    telemetry_rows = _csv_rows(checked_paths[4], errors)
    telemetry_names = [row.get("filename", "").strip() for row in telemetry_rows]
    if len([name for name in telemetry_names if name]) != len(set(name for name in telemetry_names if name)):
        errors.append("duplicate_filename:chain_phase_telemetry.csv")

    failure_rows = _csv_rows(checked_paths[5], errors)
    failure_names = [row.get("filename", "").strip() for row in failure_rows]
    if len([name for name in failure_names if name]) != len(set(name for name in failure_names if name)):
        errors.append("duplicate_filename:batch_failure_summary.csv")
    for row in failure_rows:
        log_file = row.get("log_file", "").strip()
        if log_file and not (root / log_file).is_file() and not Path(log_file).is_file():
            errors.append(f"missing_referenced_log:{log_file}")

    if errors:
        status = "invalid"
    elif stale_reasons:
        status = "stale/mixed-run"
    elif stage != "complete":
        status = "incomplete"
    else:
        status = "complete"

    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id or None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_count": input_count,
        "processed_count": result_count,
        "source_report": str(checkpoint_path),
        "checked_reports": [path.name for path in checked_paths if path.is_file()],
        "status": status,
        "stage": stage or None,
        "errors": errors,
        "stale_reasons": stale_reasons,
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "reports_dir",
        nargs="?",
        default="artifacts/converted_images/reports",
        help="Directory containing conversion reports.",
    )
    parser.add_argument("--output", type=Path, help="Optional JSON result path.")
    args = parser.parse_args(argv)
    report = evaluate_report_consistency(args.reports_dir)
    serialized = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 1 if report["status"] in EXIT_FAILURE_STATUSES else 0


if __name__ == "__main__":
    raise SystemExit(main())
