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


def test_ac0820_l_committed_svg_preserves_co2_badge_quality() -> None:
    record = review_variant("AC0820_L", source="successful_conversion")

    assert record.status == "ok"
    assert record.width == 30
    assert record.height == 30
    assert record.mean_delta2 is not None
    assert record.mean_delta2 == pytest.approx(7458.4033203125)
    assert record.normalized_mse is not None
    assert record.normalized_mse < 0.045945679012345676

    svg = Path(record.svg_path).read_text(encoding="utf-8")
    assert svg.count("<circle") == 1
    assert ">CO</text>" in svg
    assert ">2</text>" in svg
    assert "<line" not in svg


def test_ac0531_1_s_committed_svg_preserves_flap_primitives_and_quality() -> None:
    record = review_variant("AC0531_1_S", source="diff_inventory")

    assert record.status == "ok"
    assert record.width == 20
    assert record.height == 40
    assert record.mean_delta2 == pytest.approx(4837.7900390625)
    assert record.normalized_mse is not None
    assert record.normalized_mse < 0.045945679012345676

    svg = Path(record.svg_path).read_text(encoding="utf-8")
    assert svg.count("<line") == 1
    assert svg.count("<circle") == 1
    assert 'fill="#e' in svg


def test_ac0502_1_m_committed_svg_preserves_rotated_flap_quality() -> None:
    record = review_variant("AC0502_1_M", source="diff_inventory")

    assert record.status == "ok"
    assert record.width == 60
    assert record.height == 30
    assert record.mean_delta2 == pytest.approx(3126.66162109375)
    assert record.normalized_mse is not None
    assert record.normalized_mse < 0.045945679012345676

    svg = Path(record.svg_path).read_text(encoding="utf-8")
    assert svg.count("<line") == 1
    assert svg.count("<circle") == 1
    assert 'x1="0.5" y1="0.5" x2="59" y2="29"' in svg
    assert 'stroke="#e5e5e4"' in svg
    assert 'fill="#ec' in svg


def test_ac0403_1_m_committed_svg_preserves_rotated_pump_quality() -> None:
    record = review_variant("AC0403_1_M", source="diff_inventory")

    assert record.status == "ok"
    assert record.width == 30
    assert record.height == 30
    assert record.mean_delta2 == pytest.approx(4297.87890625)
    assert record.normalized_mse is not None
    assert record.normalized_mse < 0.045945679012345676

    svg = Path(record.svg_path).read_text(encoding="utf-8")
    assert svg.count("<ellipse") == 1
    assert svg.count("<polygon") == 1
    assert 'id="pump_circle"' in svg
    assert 'id="pump_triangle"' in svg


def test_ac0253_1_committed_svg_preserves_rotated_pump_quality() -> None:
    record = review_variant("AC0253_1", source="diff_inventory")

    assert record.status == "ok"
    assert record.width == 31
    assert record.height == 31
    assert record.mean_delta2 == pytest.approx(3327.90625)
    assert record.normalized_mse is not None
    assert record.normalized_mse < 0.045945679012345676

    svg = Path(record.svg_path).read_text(encoding="utf-8")
    assert svg.count("<ellipse") == 1
    assert svg.count("<polygon") == 1
    assert 'id="pump_circle"' in svg
    assert 'id="pump_triangle"' in svg


def test_ac0150_2_committed_svg_preserves_saturated_chevron_quality() -> None:
    record = review_variant("AC0150_2", source="diff_inventory")

    assert record.status == "ok"
    assert record.width == 40
    assert record.height == 80
    assert record.mean_delta2 == pytest.approx(7988.3642578125)
    assert record.normalized_mse is not None
    assert record.normalized_mse < 0.045945679012345676

    svg = Path(record.svg_path).read_text(encoding="utf-8")
    assert svg.count("<path") == 1
    assert svg.count("<line") == 0
    assert 'stroke="#f9fbf7"' in svg
    assert 'fill="#59b167"' in svg


def test_ac0551_1_m_committed_svg_preserves_chevron_quality() -> None:
    record = review_variant("AC0551_1_M", source="diff_inventory")

    assert record.status == "ok"
    assert record.width == 30
    assert record.height == 60
    assert record.mean_delta2 == pytest.approx(4518.55712890625)
    assert record.normalized_mse is not None
    assert record.normalized_mse < 0.045945679012345676

    svg = Path(record.svg_path).read_text(encoding="utf-8")
    assert svg.count("<path") == 1
    assert svg.count("<line") == 0
    assert 'stroke="#e6e6e5"' in svg
    assert 'fill="#e5' in svg


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


def test_ac0130_m_committed_svg_preserves_visible_vertical_partition_quality() -> None:
    record = review_variant("AC0130_M", source="diff_inventory")

    assert record.status == "ok"
    assert record.width == 30
    assert record.height == 60
    assert record.svg_path == "artifacts/converted_images/converted_svgs/AC0130_M.svg"
    assert record.mean_delta2 == pytest.approx(300.1560974121094)
    assert record.normalized_mse is not None
    assert record.normalized_mse < 0.045945679012345676

    svg = Path(record.svg_path).read_text(encoding="utf-8")
    assert '<g id="metal_gradient">' in svg
    assert '<path id="top_border"' in svg
    assert '<path id="bottom_border"' in svg
    assert 'id="left_partition_1"' in svg
    assert 'id="center_partition"' in svg
    assert 'id="right_partition"' in svg


def test_ac0130_committed_svg_preserves_full_size_cross_quality() -> None:
    record = review_variant("AC0130", source="diff_inventory")

    assert record.status == "ok"
    assert record.width == 40
    assert record.height == 80
    assert record.svg_path == "artifacts/converted_images/converted_svgs/AC0130.svg"
    assert record.mean_delta2 == pytest.approx(1921.981201171875)
    assert record.normalized_mse is not None
    assert record.normalized_mse < 0.045945679012345676

    svg = Path(record.svg_path).read_text(encoding="utf-8")
    assert '<g id="metal_gradient">' in svg
    assert '<rect id="main_rect"' in svg
    assert 'id="diagonal_1_tl_br"' in svg
    assert 'id="diagonal_2_tr_bl"' in svg
    assert 'id="minus_glyph_1"' in svg
    assert 'id="minus_glyph_2"' in svg
    assert "<image" not in svg


def test_ac0551_2_m_committed_svg_preserves_chevron_quality() -> None:
    record = review_variant("AC0551_2_M", source="diff_inventory")

    assert record.status == "ok"
    assert record.width == 30
    assert record.height == 60
    assert record.mean_delta2 == pytest.approx(3294.235595703125)
    assert record.normalized_mse is not None
    assert record.normalized_mse < 0.045945679012345676

    svg = Path(record.svg_path).read_text(encoding="utf-8")
    assert svg.count("<path") == 1
    assert svg.count("<line") == 0
    assert 'stroke="#e7e6e7"' in svg
    assert 'fill="#4c' in svg


def test_ac0254_2_committed_svg_preserves_left_rotated_circular_damper_quality() -> None:
    record = review_variant("AC0254_2", source="diff_inventory")

    assert record.status == "ok"
    assert record.width == 31
    assert record.height == 31
    assert record.mean_delta2 == pytest.approx(587.0509643554688)
    assert record.normalized_mse is not None
    assert record.normalized_mse < 0.045945679012345676

    svg = Path(record.svg_path).read_text(encoding="utf-8")
    assert 'id="left_rotated_circular_damper_circle"' in svg
    assert 'id="left_rotated_circular_damper_blade"' in svg
    assert svg.count("<circle") == 1
    assert svg.count("<polygon") == 1
    assert "<image" not in svg


def test_ac0732_1_s_committed_svg_preserves_right_facing_p_kelle_quality() -> None:
    record = review_variant("AC0732_1_S", source="diff_inventory")

    assert record.status == "ok"
    assert record.width == 25
    assert record.height == 15
    assert record.mean_delta2 == pytest.approx(3659.34130859375)
    assert record.normalized_mse is not None
    assert record.normalized_mse < 0.045945679012345676

    svg = Path(record.svg_path).read_text(encoding="utf-8")
    assert 'id="right_facing_square_kelle_p_connector"' in svg
    assert 'id="right_facing_square_kelle_p_body"' in svg
    assert 'id="right_facing_square_kelle_p_label"' in svg
    assert ">P</text>" in svg
    assert "rotate(" not in svg
    assert "<image" not in svg


def test_ac0732_1_l_committed_svg_preserves_right_facing_p_kelle_quality() -> None:
    record = review_variant("AC0732_1_L", source="diff_inventory")

    assert record.status == "ok"
    assert record.width == 45
    assert record.height == 25
    assert record.mean_delta2 == pytest.approx(6015.9892578125)
    assert record.normalized_mse is not None
    assert record.normalized_mse < 0.045945679012345676

    svg = Path(record.svg_path).read_text(encoding="utf-8")
    assert 'id="right_facing_square_kelle_p_connector"' in svg
    assert 'id="right_facing_square_kelle_p_body"' in svg
    assert 'id="right_facing_square_kelle_p_label"' in svg
    assert ">P</text>" in svg
    assert "rotate(" not in svg
    assert "<image" not in svg


def test_ac0732_1_m_committed_svg_preserves_right_facing_p_kelle_quality() -> None:
    record = review_variant("AC0732_1_M", source="diff_inventory")

    assert record.status == "ok"
    assert record.width == 35
    assert record.height == 20
    assert record.mean_delta2 == pytest.approx(3317.628662109375)
    assert record.normalized_mse is not None
    assert record.normalized_mse < 0.045945679012345676

    svg = Path(record.svg_path).read_text(encoding="utf-8")
    assert 'id="right_facing_square_kelle_p_connector"' in svg
    assert 'id="right_facing_square_kelle_p_body"' in svg
    assert 'id="right_facing_square_kelle_p_label"' in svg
    assert ">P</text>" in svg
    assert "rotate(" not in svg
    assert "<image" not in svg


def test_ac0733_1_l_committed_svg_preserves_horizontal_p_kelle_quality() -> None:
    record = review_variant("AC0733_1_L", source="diff_inventory")

    assert record.status == "ok"
    assert record.width == 25
    assert record.height == 45
    assert record.mean_delta2 == pytest.approx(2707.703125)
    assert record.normalized_mse is not None
    assert record.normalized_mse < 0.045945679012345676

    svg = Path(record.svg_path).read_text(encoding="utf-8")
    assert 'id="right_rotated_square_kelle_p_connector"' in svg
    assert 'id="right_rotated_square_kelle_p_body"' in svg
    assert 'id="right_rotated_square_kelle_p_label"' in svg
    assert ">P</text>" in svg
    assert "rotate(" not in svg
    assert "<image" not in svg


def test_ac0733_1_m_committed_svg_preserves_horizontal_p_kelle_quality() -> None:
    record = review_variant("AC0733_1_M", source="diff_inventory")

    assert record.status == "ok"
    assert record.width == 20
    assert record.height == 35
    assert record.mean_delta2 == pytest.approx(3555.33154296875)
    assert record.normalized_mse is not None
    assert record.normalized_mse < 0.045945679012345676

    svg = Path(record.svg_path).read_text(encoding="utf-8")
    assert 'id="right_rotated_square_kelle_p_connector"' in svg
    assert 'id="right_rotated_square_kelle_p_body"' in svg
    assert 'id="right_rotated_square_kelle_p_label"' in svg
    assert ">P</text>" in svg
    assert "rotate(" not in svg
    assert "<image" not in svg


def test_ac0722_1_l_committed_svg_preserves_horizontal_t_kelle_quality() -> None:
    record = review_variant("AC0722_1_L", source="diff_inventory")

    assert record.status == "ok"
    assert record.width == 45
    assert record.height == 25
    assert record.mean_delta2 == pytest.approx(4721.47900390625)
    assert record.normalized_mse is not None
    assert record.normalized_mse < 0.045945679012345676

    svg = Path(record.svg_path).read_text(encoding="utf-8")
    assert 'id="left_rotated_square_kelle_t_connector"' in svg
    assert 'id="left_rotated_square_kelle_t_body"' in svg
    assert 'id="left_rotated_square_kelle_t_label"' in svg
    assert ">T</text>" in svg
    assert "rotate(" not in svg
    assert "<image" not in svg


def test_ac0723_1_s_committed_svg_preserves_vertical_square_t_kelle_quality() -> None:
    record = review_variant("AC0723_1_S", source="diff_inventory")

    assert record.status == "ok"
    assert record.width == 15
    assert record.height == 25
    assert record.mean_delta2 == pytest.approx(2197.709228515625)
    assert record.normalized_mse is not None
    assert record.normalized_mse < 0.045945679012345676

    svg = Path(record.svg_path).read_text(encoding="utf-8")
    assert 'id="vertically_mirrored_square_kelle_t_connector"' in svg
    assert 'id="vertically_mirrored_square_kelle_t_body"' in svg
    assert 'id="vertically_mirrored_square_kelle_t_label"' in svg
    assert ">T</text>" in svg
    assert "rotate(" not in svg
    assert "<image" not in svg


def test_ac0701_1_s_committed_svg_preserves_upright_square_kelle_quality() -> None:
    record = review_variant("AC0701_1_S", source="diff_inventory")

    assert record.status == "ok"
    assert record.width == 15
    assert record.height == 25
    assert record.mean_delta2 == pytest.approx(560.10400390625)
    assert record.normalized_mse is not None
    assert record.normalized_mse < 0.045945679012345676

    svg = Path(record.svg_path).read_text(encoding="utf-8")
    assert 'id="upright_square_kelle_connector"' in svg
    assert 'id="upright_square_kelle_body"' in svg
    assert svg.count("<rect") == 1
    assert svg.count("<path") == 1
    assert "<text" not in svg
    assert "rotate(" not in svg
    assert "<image" not in svg
