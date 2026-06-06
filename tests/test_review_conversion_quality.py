from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from tools.review_conversion_quality import (
    QualityRecord,
    normalized_mse,
    select_plan_b_candidates,
    write_reports,
)


def _record(
    variant: str,
    mse: float | None,
    *,
    source: str,
    status: str = "ok",
    width: int = 25,
    height: int = 25,
) -> QualityRecord:
    return QualityRecord(
        variant=variant,
        source=source,
        image_path=f"images/{variant}.jpg",
        svg_path=f"svgs/{variant}.svg",
        width=width,
        height=height,
        mean_delta2=None if mse is None else mse * 3 * 255 * 255,
        normalized_mse=mse,
        status=status,
    )


def test_normalized_mse_uses_three_channel_rgb_range() -> None:
    image = np.zeros((2, 2, 3), dtype=np.uint8)
    rendered = np.full((2, 2, 3), 255, dtype=np.uint8)

    mean_delta2, mse = normalized_mse(image, rendered)

    assert mean_delta2 == 3 * 255 * 255
    assert mse == 1.0


def test_select_plan_b_candidates_prioritizes_failed_success_then_compact_diffs() -> None:
    successful = [
        _record("AC_GOOD", 0.01, source="successful_conversion"),
        _record("AC_BAD", 0.06, source="successful_conversion"),
        _record("AC_MISSING", None, source="successful_conversion", status="missing_pair"),
    ]
    diffs = [
        _record("AC_DIFF_HIGH", 0.3, source="diff_inventory"),
        _record("AC_DIFF_LOW", 0.04, source="diff_inventory"),
        _record("AC_DIFF_LARGE", 0.4, source="diff_inventory", width=100, height=100),
        _record("AC_DIFF_sia", 0.5, source="diff_inventory"),
    ]

    selected = select_plan_b_candidates(
        successful,
        diffs,
        threshold=0.05,
        max_candidates=3,
        max_image_area=3_200,
    )

    assert [record.variant for record in selected] == [
        "AC_MISSING",
        "AC_BAD",
        "AC_DIFF_HIGH",
    ]


def test_write_reports_keeps_candidate_priority_machine_readable(tmp_path: Path) -> None:
    successful = [_record("AC_BAD", 0.06, source="successful_conversion")]
    diffs = [_record("AC_DIFF", 0.2, source="diff_inventory")]

    summary = write_reports(
        tmp_path,
        successful,
        diffs,
        [successful[0], diffs[0]],
        threshold=0.05,
        max_image_area=3_200,
    )

    assert summary["metrics"]["selected_candidates"] == 2
    report = json.loads((tmp_path / "conversion_quality_review_v2.json").read_text())
    assert [item["variant"] for item in report["selected_candidates"]] == [
        "AC_BAD",
        "AC_DIFF",
    ]
    rows = list(csv.DictReader((tmp_path / "plan_b_candidate_triage_v1.csv").open()))
    assert [row["priority"] for row in rows] == ["1", "2"]
