from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pytest

from tools.review_conversion_quality import (
    QualityRecord,
    normalized_mse,
    review_variant,
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


def test_ac0835_l_committed_svg_is_below_review_threshold() -> None:
    record = review_variant("AC0835_L", source="successful_conversion")

    assert record.status == "ok"
    assert record.width == 25
    assert record.height == 25
    assert record.mean_delta2 is not None
    assert record.mean_delta2 == pytest.approx(7629.90234375)
    assert record.normalized_mse is not None
    assert record.normalized_mse < 0.045945679012345676


def test_ac0922_s_committed_snapshot_preserves_circle_connector_quality() -> None:
    record = review_variant("AC0922_S", source="diff_inventory")

    assert record.status == "ok"
    assert record.width == 25
    assert record.height == 15
    assert record.svg_path == (
        "artifacts/converted_images/reports/conversion_bestlist_snapshots/AC0922_S.svg"
    )
    assert record.mean_delta2 == pytest.approx(5359.11181640625)
    assert record.normalized_mse is not None
    assert record.normalized_mse < 0.045945679012345676

    svg = Path(record.svg_path).read_text(encoding="utf-8")
    assert "<circle" in svg
    assert "<line" in svg


def test_ac0414_s_committed_svg_preserves_partitioned_circle_quality() -> None:
    record = review_variant("AC0414_S", source="diff_inventory")

    assert record.status == "ok"
    assert record.width == 20
    assert record.height == 20
    assert record.svg_path == "artifacts/converted_images/converted_svgs/AC0414_S.svg"
    assert record.mean_delta2 == pytest.approx(703.8825073242188)
    assert record.normalized_mse is not None
    assert record.normalized_mse < 0.045945679012345676

    svg = Path(record.svg_path).read_text(encoding="utf-8")
    assert '<circle id="partitioned_circle"' in svg
    assert '<g id="partition_lines"' in svg
    assert svg.count(" M ") == 3
