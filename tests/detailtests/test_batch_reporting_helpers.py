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
