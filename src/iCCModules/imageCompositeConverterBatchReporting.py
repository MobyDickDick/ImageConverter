"""Batch/reporting helper functions extracted from imageCompositeConverter."""

from __future__ import annotations

import csv
import math
import os


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
