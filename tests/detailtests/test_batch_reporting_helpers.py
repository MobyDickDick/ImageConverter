from __future__ import annotations

import csv
from pathlib import Path

from src.iCCModules import imageCompositeConverterBatchReporting as helpers


def test_write_batch_failure_summary_writes_expected_columns(tmp_path: Path):
    helpers.writeBatchFailureSummaryImpl(
        reports_out_dir=str(tmp_path),
        failures=[
            {
                "filename": "AC0800_S.jpg",
                "status": "semantic_mismatch",
                "reason": "semantic_mismatch",
                "details": "circle missing",
                "log_file": "AC0800_S_element_validation.log",
            }
        ],
    )

    out_path = tmp_path / "batch_failure_summary.csv"
    with out_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle, delimiter=";"))

    assert rows[0] == ["filename", "status", "reason", "details", "log_file"]
    assert rows[1] == [
        "AC0800_S.jpg",
        "semantic_mismatch",
        "semantic_mismatch",
        "circle missing",
        "AC0800_S_element_validation.log",
    ]


def test_write_strategy_switch_template_transfers_report_formats_values(tmp_path: Path):
    helpers.writeStrategySwitchTemplateTransfersImpl(
        reports_out_dir=str(tmp_path),
        strategy_rows=[
            {
                "filename": "AC0811_S.jpg",
                "donor_variant": "AC0811_M",
                "rotation_deg": 90,
                "scale": 1.23456,
                "old_error_per_pixel": 0.123456789,
                "new_error_per_pixel": 0.012345678,
            }
        ],
    )

    out_path = tmp_path / "strategy_switch_template_transfers.csv"
    with out_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle, delimiter=";"))

    assert rows[0] == [
        "filename",
        "donor_variant",
        "rotation_deg",
        "scale",
        "old_error_per_pixel",
        "new_error_per_pixel",
    ]
    assert rows[1] == [
        "AC0811_S.jpg",
        "AC0811_M",
        "90",
        "1.2346",
        "0.12345679",
        "0.01234568",
    ]


def test_write_chain_telemetry_batch_report_writes_rows_and_aggregate(tmp_path: Path):
    result_map = {
        "AC0130_M.jpg": {
            "variant": "AC0130_M",
            "status": "semantic_ok",
            "error_per_pixel": 0.012345678,
            "mean_delta2": 12.5,
            "params": {
                "chain_phase_telemetry": {
                    "geometry_phase": "geometry_chain.elementwise",
                    "geometry_phase_mode": "elementwise_geometry_ir",
                    "policy_phase": "policy.reference_selected",
                    "policy_phase_decision": "sample_wins",
                    "step_count": 2,
                    "step_accepted_count": 1,
                    "step_success_rate": 0.5,
                    "override_applied": True,
                    "override_reason": "sample_better",
                    "placeholder_emergency_used": False,
                }
            },
        }
    }

    csv_path, txt_path, rows = helpers.writeChainTelemetryBatchReportImpl(
        str(tmp_path),
        result_map,
        lambda telemetry_rows: {
            "conversion_count": len(telemetry_rows),
            "mean_step_success_rate": 0.5,
            "override_frequency": 1.0,
            "placeholder_emergency_rate": 0.0,
        },
    )

    assert rows[0]["variant"] == "AC0130_M"
    with Path(csv_path).open("r", encoding="utf-8", newline="") as handle:
        csv_rows = list(csv.reader(handle, delimiter=";"))
    assert csv_rows[0] == [
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
    assert csv_rows[1] == [
        "AC0130_M",
        "AC0130_M.jpg",
        "semantic_ok",
        "0.012346",
        "12.500000",
        "geometry_chain.elementwise",
        "elementwise_geometry_ir",
        "policy.reference_selected",
        "sample_wins",
        "2",
        "1",
        "0.500000",
        "1",
        "sample_better",
        "0",
    ]
    summary = Path(txt_path).read_text(encoding="utf-8")
    assert "conversion_count=1" in summary
    assert "override_frequency=1.0" in summary
    assert "semantic_ok_count=1" in summary
    assert "non_green_count=0" in summary
    assert "mean_error_per_pixel=0.012346" in summary
    assert "mean_delta2=12.500000" in summary


def test_write_chain_telemetry_batch_report_marks_drift_pass(tmp_path: Path):
    result_map = {
        "AC0120_S.jpg": {
            "variant": "AC0120_S",
            "status": "semantic_ok",
            "error_per_pixel": 0.01,
            "mean_delta2": 10.0,
            "params": {"chain_phase_telemetry": {"step_success_rate": 1.0}},
        }
    }

    _csv_path, txt_path, _rows = helpers.writeChainTelemetryBatchReportImpl(
        str(tmp_path),
        result_map,
        lambda _telemetry_rows: {},
    )

    summary = Path(txt_path).read_text(encoding="utf-8")
    assert "drift_status=pass" in summary
    assert "drift_reasons=" in summary
    assert "drift_max_mean_error_per_pixel=0.050000" in summary
    assert "drift_max_mean_delta2=18.000000" in summary
    assert "drift_max_non_green=0" in summary


def test_write_chain_telemetry_batch_report_marks_drift_warning(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ICC_CHAIN_DRIFT_MAX_MEAN_ERROR_PER_PIXEL", "0.02")
    monkeypatch.setenv("ICC_CHAIN_DRIFT_MAX_MEAN_DELTA2", "20.0")
    monkeypatch.setenv("ICC_CHAIN_DRIFT_MAX_NON_GREEN", "0")
    result_map = {
        "AC0120_L.jpg": {
            "variant": "AC0120_L",
            "status": "semantic_mismatch",
            "error_per_pixel": 0.03,
            "mean_delta2": 25.0,
            "params": {"chain_phase_telemetry": {"step_success_rate": 0.0}},
        }
    }

    _csv_path, txt_path, _rows = helpers.writeChainTelemetryBatchReportImpl(
        str(tmp_path),
        result_map,
        lambda _telemetry_rows: {},
    )

    summary = Path(txt_path).read_text(encoding="utf-8")
    assert "drift_status=warn" in summary
    assert (
        "drift_reasons=mean_error_per_pixel_above_limit,"
        "mean_delta2_above_limit,non_green_count_above_limit"
    ) in summary
    assert "drift_max_mean_error_per_pixel=0.020000" in summary
    assert "drift_max_mean_delta2=20.000000" in summary
