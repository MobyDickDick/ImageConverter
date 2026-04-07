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
