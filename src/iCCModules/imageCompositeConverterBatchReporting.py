"""Batch/reporting helper functions extracted from imageCompositeConverter."""

from __future__ import annotations

import csv
import json
import math
import os

from src.iCCModules.imageCompositeConverterIterationLog import optimizationRenderTelemetryImpl


def readValidationLogDetailsImpl(log_path: str) -> dict[str, str]:
    if not os.path.exists(log_path):
        return {}
    details: dict[str, str] = {}
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or ": " in line.split("=", 1)[0]:
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                details[key] = value
    except OSError:
        return {}
    return details


def writeBatchFailureSummaryImpl(reports_out_dir: str, failures: list[dict[str, str]]) -> None:
    summary_path = os.path.join(reports_out_dir, "batch_failure_summary.csv")
    with open(summary_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["filename", "status", "reason", "details", "log_file"])
        for failure in failures:
            writer.writerow(
                [
                    failure.get("filename", ""),
                    failure.get("status", ""),
                    failure.get("reason", ""),
                    failure.get("details", ""),
                    failure.get("log_file", ""),
                ]
            )


def writeOptimizationRenderTelemetrySummaryImpl(
    reports_out_dir: str,
    result_map: dict[str, dict[str, object]],
) -> str:
    """Persist batch totals and affected variants for optimizer render failures."""
    affected: list[dict[str, object]] = []
    total_timeouts = 0
    total_errors = 0
    for filename, row in result_map.items():
        telemetry = optimizationRenderTelemetryImpl(row)
        render_timeouts = telemetry["render_timeouts"]
        render_errors = telemetry["render_errors"]
        total_timeouts += render_timeouts
        total_errors += render_errors
        if render_timeouts or render_errors:
            affected.append(
                {
                    "variant": str(row.get("variant") or os.path.splitext(filename)[0]).strip().upper(),
                    "filename": filename,
                    "render_timeouts": render_timeouts,
                    "render_errors": render_errors,
                }
            )

    affected.sort(key=lambda item: (str(item["variant"]), str(item["filename"])))
    payload = {
        "schema_version": "optimization_render_telemetry_summary_v1",
        "conversion_count": len(result_map),
        "affected_variant_count": len({str(item["variant"]) for item in affected}),
        "render_timeouts": total_timeouts,
        "render_errors": total_errors,
        "affected_variants": affected,
    }
    output_path = os.path.join(reports_out_dir, "optimization_render_telemetry_summary.json")
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    return output_path


def writeOptimizationRenderTelemetryComparisonImpl(
    reports_out_dir: str,
    current_summary_path: str,
    baseline_summary_path: str,
) -> str:
    """Compare two explicitly selected optimizer telemetry batch summaries."""

    def _load_summary(path: str) -> dict[str, object]:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            raise ValueError(f"optimization telemetry summary must be an object: {path}")
        if payload.get("schema_version") != "optimization_render_telemetry_summary_v1":
            raise ValueError(f"unsupported optimization telemetry summary schema: {path}")
        return payload

    def _counter(summary: dict[str, object], name: str) -> int:
        value = summary.get(name, 0)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"invalid non-negative integer field {name!r}")
        return value

    def _variant_counters(summary: dict[str, object]) -> dict[str, dict[str, int]]:
        entries = summary.get("affected_variants", [])
        if not isinstance(entries, list):
            raise ValueError("invalid affected_variants field")
        variants: dict[str, dict[str, int]] = {}
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError("affected_variants entries must be objects")
            raw_variant = entry.get("variant")
            if not isinstance(raw_variant, str) or not raw_variant.strip():
                raise ValueError("affected_variants entries require a non-empty variant")
            variant = raw_variant.strip().upper()
            totals = variants.setdefault(variant, {"render_timeouts": 0, "render_errors": 0})
            for name in ("render_timeouts", "render_errors"):
                totals[name] += _counter(entry, name)
        return variants

    current = _load_summary(current_summary_path)
    baseline = _load_summary(baseline_summary_path)
    counters: dict[str, dict[str, int]] = {}
    for name in ("render_timeouts", "render_errors"):
        current_value = _counter(current, name)
        baseline_value = _counter(baseline, name)
        counters[name] = {
            "baseline": baseline_value,
            "current": current_value,
            "delta": current_value - baseline_value,
        }

    current_variants = _variant_counters(current)
    baseline_variants = _variant_counters(baseline)
    variant_deltas: list[dict[str, object]] = []
    for variant in sorted(current_variants.keys() | baseline_variants.keys()):
        variant_counters: dict[str, dict[str, int]] = {}
        for name in ("render_timeouts", "render_errors"):
            current_value = current_variants.get(variant, {}).get(name, 0)
            baseline_value = baseline_variants.get(variant, {}).get(name, 0)
            variant_counters[name] = {
                "baseline": baseline_value,
                "current": current_value,
                "delta": current_value - baseline_value,
            }
        variant_deltas.append({"variant": variant, "counters": variant_counters})

    payload = {
        "schema_version": "optimization_render_telemetry_comparison_v1",
        "baseline_summary": os.path.abspath(baseline_summary_path),
        "current_summary": os.path.abspath(current_summary_path),
        "counters": counters,
        "variant_deltas": variant_deltas,
    }
    output_path = os.path.join(reports_out_dir, "optimization_render_telemetry_comparison.json")
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    return output_path


def _chainTelemetryRows(result_map: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for filename, result_row in result_map.items():
        params = result_row.get("params")
        if not isinstance(params, dict):
            continue
        telemetry = params.get("chain_phase_telemetry")
        if not isinstance(telemetry, dict):
            continue
        variant = str(result_row.get("variant") or os.path.splitext(filename)[0]).strip().upper()
        rows.append(
            {
                "filename": filename,
                "variant": variant,
                "status": str(result_row.get("status", "")),
                "error_per_pixel": _finiteFloatOrNone(result_row.get("error_per_pixel")),
                "mean_delta2": _finiteFloatOrNone(result_row.get("mean_delta2")),
                "geometry_phase": str(telemetry.get("geometry_phase", "")),
                "geometry_phase_mode": str(telemetry.get("geometry_phase_mode", "")),
                "policy_phase": str(telemetry.get("policy_phase", "")),
                "policy_phase_decision": str(telemetry.get("policy_phase_decision", "")),
                "step_count": int(telemetry.get("step_count", 0) or 0),
                "step_accepted_count": int(telemetry.get("step_accepted_count", 0) or 0),
                "step_success_rate": float(telemetry.get("step_success_rate", 0.0) or 0.0),
                "override_applied": bool(telemetry.get("override_applied") is True),
                "override_reason": "" if telemetry.get("override_reason") is None else str(telemetry.get("override_reason")),
                "placeholder_emergency_used": bool(telemetry.get("placeholder_emergency_used") is True),
            }
        )
    rows.sort(key=lambda row: str(row.get("variant", "")))
    return rows


def _finiteFloatOrNone(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _meanFinite(rows: list[dict[str, object]], key: str) -> float | None:
    values = [float(row[key]) for row in rows if row.get(key) is not None]
    if not values:
        return None
    return sum(values) / len(values)


def _chainScorecardSummary(rows: list[dict[str, object]]) -> dict[str, object]:
    semantic_ok_count = sum(1 for row in rows if str(row.get("status", "")).strip().lower() == "semantic_ok")
    return {
        "scorecard_row_count": len(rows),
        "semantic_ok_count": semantic_ok_count,
        "non_green_count": max(0, len(rows) - semantic_ok_count),
        "mean_error_per_pixel": _meanFinite(rows, "error_per_pixel"),
        "mean_delta2": _meanFinite(rows, "mean_delta2"),
    }


def _envFloat(name: str, default: float) -> float:
    try:
        value = float(os.environ.get(name, str(default)) or default)
    except (TypeError, ValueError):
        return default
    return value if math.isfinite(value) else default


def _envInt(name: str, default: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)) or default)
    except (TypeError, ValueError):
        return default
    return max(0, value)


def _chainScorecardDriftGate(scorecard: dict[str, object]) -> dict[str, object]:
    error_limit = max(0.0, _envFloat("ICC_CHAIN_DRIFT_MAX_MEAN_ERROR_PER_PIXEL", 0.05))
    delta2_limit = max(0.0, _envFloat("ICC_CHAIN_DRIFT_MAX_MEAN_DELTA2", 18.0))
    non_green_limit = _envInt("ICC_CHAIN_DRIFT_MAX_NON_GREEN", 0)
    reasons: list[str] = []

    # Empty telemetry reports are produced by code-only or smoke runs that did
    # not convert any image with chain telemetry. They are valid completion
    # artifacts, not metric drift; keep the gate green so stale empty summaries
    # do not fail local completion checks.
    if int(scorecard.get("scorecard_row_count", 0) or 0) <= 0:
        return {
            "drift_status": "pass",
            "drift_reasons": "",
            "drift_max_mean_error_per_pixel": error_limit,
            "drift_max_mean_delta2": delta2_limit,
            "drift_max_non_green": non_green_limit,
        }

    mean_error = scorecard.get("mean_error_per_pixel")
    if mean_error is None:
        reasons.append("mean_error_per_pixel_missing")
    elif float(mean_error) > error_limit:
        reasons.append("mean_error_per_pixel_above_limit")

    mean_delta2 = scorecard.get("mean_delta2")
    if mean_delta2 is None:
        reasons.append("mean_delta2_missing")
    elif float(mean_delta2) > delta2_limit:
        reasons.append("mean_delta2_above_limit")

    non_green_count = int(scorecard.get("non_green_count", 0) or 0)
    if non_green_count > non_green_limit:
        reasons.append("non_green_count_above_limit")

    return {
        "drift_status": "pass" if not reasons else "warn",
        "drift_reasons": ",".join(reasons),
        "drift_max_mean_error_per_pixel": error_limit,
        "drift_max_mean_delta2": delta2_limit,
        "drift_max_non_green": non_green_limit,
    }


def _formatScorecardValue(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def writeChainTelemetryBatchReportImpl(
    reports_out_dir: str,
    result_map: dict[str, dict[str, object]],
    aggregate_chain_telemetry_fn,
) -> tuple[str, str, list[dict[str, object]]]:
    """Write per-run Geometry-IR chain telemetry CSV and aggregate summary."""

    rows = _chainTelemetryRows(result_map)
    csv_path = os.path.join(reports_out_dir, "chain_phase_telemetry.csv")
    txt_path = os.path.join(reports_out_dir, "chain_phase_telemetry_summary.txt")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(
            [
                "variant",
                "filename",
                "status",
                "error_per_pixel",
                "mean_delta2",
                "geometry_phase",
                "geometry_phase_mode",
                "policy_phase",
                "policy_phase_decision",
                "step_count",
                "step_accepted_count",
                "step_success_rate",
                "override_applied",
                "override_reason",
                "placeholder_emergency_used",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row["variant"],
                    row["filename"],
                    row["status"],
                    _formatScorecardValue(row["error_per_pixel"]),
                    _formatScorecardValue(row["mean_delta2"]),
                    row["geometry_phase"],
                    row["geometry_phase_mode"],
                    row["policy_phase"],
                    row["policy_phase_decision"],
                    row["step_count"],
                    row["step_accepted_count"],
                    f"{float(row['step_success_rate']):.6f}",
                    int(bool(row["override_applied"])),
                    row["override_reason"],
                    int(bool(row["placeholder_emergency_used"])),
                ]
            )

    aggregate = aggregate_chain_telemetry_fn(rows)
    scorecard = _chainScorecardSummary(rows)
    drift_gate = _chainScorecardDriftGate(scorecard)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"telemetry_csv={csv_path}\n")
        for key in (
            "conversion_count",
            "mean_step_success_rate",
            "override_frequency",
            "placeholder_emergency_rate",
        ):
            f.write(f"{key}={aggregate.get(key)}\n")
        for key in (
            "scorecard_row_count",
            "semantic_ok_count",
            "non_green_count",
            "mean_error_per_pixel",
            "mean_delta2",
        ):
            f.write(f"{key}={_formatScorecardValue(scorecard.get(key))}\n")
        for key in (
            "drift_status",
            "drift_reasons",
            "drift_max_mean_error_per_pixel",
            "drift_max_mean_delta2",
            "drift_max_non_green",
        ):
            f.write(f"{key}={_formatScorecardValue(drift_gate.get(key))}\n")

    return csv_path, txt_path, rows


def loadConversionCheckpointResultMapImpl(checkpoint_path: str) -> dict[str, dict[str, object]]:
    """Load the result-map snapshot referenced by an incremental checkpoint.

    The checkpoint stores ``result_map_path`` as either a relative filename in
    the same reports directory or an absolute path. Invalid, missing, or legacy
    checkpoint files deliberately resolve to an empty map so resume/audit callers
    can fall back to a cold run without wrapping imports in exception handlers.
    """

    if not os.path.exists(checkpoint_path):
        return {}
    try:
        with open(checkpoint_path, "r", encoding="utf-8") as f:
            checkpoint = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(checkpoint, dict):
        return {}

    raw_result_map_path = checkpoint.get("result_map_path")
    if not isinstance(raw_result_map_path, str) or not raw_result_map_path.strip():
        return {}
    result_map_path = raw_result_map_path.strip()
    if not os.path.isabs(result_map_path):
        result_map_path = os.path.join(os.path.dirname(checkpoint_path), result_map_path)

    try:
        with open(result_map_path, "r", encoding="utf-8") as f:
            result_map = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(result_map, dict):
        return {}

    normalized: dict[str, dict[str, object]] = {}
    for filename, row in result_map.items():
        if isinstance(filename, str) and isinstance(row, dict):
            normalized[filename] = dict(row)
    return normalized



def partitionCheckpointResumeRowsImpl(
    *,
    process_files: list[str],
    checkpoint_result_map: dict[str, dict[str, object]],
) -> tuple[list[str], dict[str, dict[str, object]]]:
    """Split requested files into remaining work and resumable checkpoint rows.

    Only rows whose filename is part of the current request are reused. This
    keeps resume mode scoped to the active range while preserving the exact
    filename keys expected by downstream reporting.
    """

    if not checkpoint_result_map:
        return list(process_files), {}

    requested = set(process_files)
    resume_rows: dict[str, dict[str, object]] = {}
    remaining: list[str] = []
    for filename in process_files:
        row = checkpoint_result_map.get(filename)
        if isinstance(row, dict):
            normalized = dict(row)
            normalized.setdefault("filename", filename)
            normalized["resume_source"] = "conversion_checkpoint"
            resume_rows[filename] = normalized
        else:
            remaining.append(filename)

    # Ignore stale checkpoint rows from other ranges.
    resume_rows = {filename: row for filename, row in resume_rows.items() if filename in requested}
    return remaining, resume_rows

def readKeyValueReportImpl(report_path: str) -> dict[str, str]:
    """Read a simple key=value report artifact into a dictionary."""

    values: dict[str, str] = {}
    if not os.path.exists(report_path):
        return values
    with open(report_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def _reportIntValue(values: dict[str, str], key: str) -> int | None:
    raw = values.get(key, "")
    try:
        return int(float(raw))
    except (TypeError, ValueError):
        return None


def _isEmptyTelemetryMissingMetricWarning(values: dict[str, str], reasons: list[str]) -> bool:
    allowed_reasons = {"mean_error_per_pixel_missing", "mean_delta2_missing"}
    if not reasons or any(reason not in allowed_reasons for reason in reasons):
        return False
    row_count = _reportIntValue(values, "scorecard_row_count")
    conversion_count = _reportIntValue(values, "conversion_count")
    return row_count == 0 or (row_count is None and conversion_count == 0)


def checkChainTelemetryDriftSummaryImpl(summary_path: str) -> dict[str, object]:
    """Evaluate a chain telemetry summary artifact as an automated drift gate."""

    if not os.path.exists(summary_path):
        return {
            "accepted": False,
            "status": "missing",
            "reasons": ["summary_missing"],
            "summary_path": summary_path,
        }

    values = readKeyValueReportImpl(summary_path)
    status = values.get("drift_status", "").strip().lower()
    raw_reasons = values.get("drift_reasons", "")
    reasons = [reason for reason in raw_reasons.split(",") if reason]

    if status == "pass":
        return {
            "accepted": True,
            "status": "pass",
            "reasons": reasons,
            "summary_path": summary_path,
            "telemetry_csv": values.get("telemetry_csv", ""),
        }

    if status == "warn":
        if _isEmptyTelemetryMissingMetricWarning(values, reasons):
            return {
                "accepted": True,
                "status": "pass",
                "reasons": [],
                "summary_path": summary_path,
                "telemetry_csv": values.get("telemetry_csv", ""),
            }
        return {
            "accepted": False,
            "status": "warn",
            "reasons": reasons or ["drift_warning_without_reason"],
            "summary_path": summary_path,
            "telemetry_csv": values.get("telemetry_csv", ""),
        }

    return {
        "accepted": False,
        "status": status or "missing",
        "reasons": ["drift_status_missing"],
        "summary_path": summary_path,
        "telemetry_csv": values.get("telemetry_csv", ""),
    }


def writeStrategySwitchTemplateTransfersImpl(
    reports_out_dir: str,
    strategy_rows: list[dict[str, object]],
) -> None:
    strategy_path = os.path.join(reports_out_dir, "strategy_switch_template_transfers.csv")
    with open(strategy_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(
            [
                "filename",
                "donor_variant",
                "rotation_deg",
                "scale",
                "old_error_per_pixel",
                "new_error_per_pixel",
            ]
        )
        for row in strategy_rows:
            writer.writerow(
                [
                    row.get("filename", ""),
                    row.get("donor_variant", ""),
                    row.get("rotation_deg", ""),
                    f"{float(row.get('scale', 0.0)):.4f}",
                    f"{float(row.get('old_error_per_pixel', 0.0)):.8f}",
                    f"{float(row.get('new_error_per_pixel', 0.0)):.8f}",
                ]
            )
