from __future__ import annotations

import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterSemanticAc0050 as ac0050_helpers

cv2 = pytest.importorskip("cv2")


def _hex_to_bgr(hex_color: str) -> tuple[int, int, int]:
    s = str(hex_color).strip()
    return (int(s[5:7], 16), int(s[3:5], 16), int(s[1:3], 16))


def _hex_channel_distance(a: str, b: str) -> int:
    aa = a.strip().lstrip("#")
    bb = b.strip().lstrip("#")
    return max(abs(int(aa[i : i + 2], 16) - int(bb[i : i + 2], 16)) for i in (0, 2, 4))


def _synthetic_input(width: int, height: int, geometry: ac0050_helpers.Ac0050Geometry) -> np.ndarray:
    img = np.full((height, width, 3), 255, dtype=np.uint8)
    lw = int(round(geometry.line_width))
    cv2.line(
        img,
        (int(round(geometry.left_x)), int(round(geometry.line_top))),
        (int(round(geometry.left_x)), int(round(geometry.line_bottom))),
        _hex_to_bgr(geometry.left_line_color),
        lw,
    )
    cv2.line(
        img,
        (int(round(geometry.right_x)), int(round(geometry.line_top))),
        (int(round(geometry.right_x)), int(round(geometry.line_bottom))),
        _hex_to_bgr(geometry.right_line_color),
        lw,
    )
    left_tri = np.array(
        [
            [int(round(geometry.left_x - geometry.triangle_half_base)), int(round(geometry.line_bottom))],
            [int(round(geometry.left_x + geometry.triangle_half_base)), int(round(geometry.line_bottom))],
            [int(round(geometry.left_x)), int(round(geometry.line_bottom + geometry.triangle_height))],
        ],
        dtype=np.int32,
    )
    right_tri = np.array(
        [
            [int(round(geometry.right_x - geometry.triangle_half_base)), int(round(geometry.line_bottom))],
            [int(round(geometry.right_x + geometry.triangle_half_base)), int(round(geometry.line_bottom))],
            [int(round(geometry.right_x)), int(round(geometry.line_bottom + geometry.triangle_height))],
        ],
        dtype=np.int32,
    )
    cv2.fillPoly(img, [left_tri], _hex_to_bgr(geometry.left_triangle_color))
    cv2.fillPoly(img, [right_tri], _hex_to_bgr(geometry.right_triangle_color))
    return img


def test_default_ac0050_geometry_stays_inside_canvas() -> None:
    geometry = ac0050_helpers.defaultAc0050GeometryImpl(40, 140)

    assert 0.0 <= geometry.left_x < geometry.right_x <= 39.0
    assert geometry.line_top == 0.0
    assert 0.0 < geometry.line_bottom < 140.0
    assert geometry.triangle_height > 0.0


def test_generate_svg_contains_expected_core_primitives() -> None:
    geometry = ac0050_helpers.defaultAc0050GeometryImpl(40, 140)
    svg = ac0050_helpers.generateAc0050SvgImpl(40, 140, geometry)

    assert 'viewBox="0 0 40 140"' in svg
    assert "#e85b57" in svg
    assert "#4e93c1" in svg
    assert svg.count("<path") == 4


def test_measure_and_draw_detects_dual_stems_and_samples_colors() -> None:
    known = ac0050_helpers.Ac0050Geometry(
        left_x=6.0,
        right_x=34.0,
        line_top=0.0,
        line_bottom=130.0,
        line_width=2.0,
        triangle_half_base=5.0,
        triangle_height=10.0,
    )
    img = _synthetic_input(40, 140, known)

    measured, svg, logs = ac0050_helpers.measureAndDrawAc0050Impl(img, cv2_module=cv2, np_module=np)

    assert abs(measured.left_x - known.left_x) <= 2.0
    assert abs(measured.right_x - known.right_x) <= 2.0
    assert measured.line_bottom >= 126.0
    assert measured.triangle_height >= 6.0
    assert measured.left_line_color.startswith("#")
    assert measured.right_triangle_color.startswith("#")
    assert "ac0050: measured" in "\n".join(logs)
    assert "<svg" in svg


@pytest.mark.parametrize(
    ("width", "height", "left_x", "right_x", "line_bottom", "tri_h"),
    [
        (40, 140, 6.0, 34.0, 130.0, 10.0),
        (80, 220, 14.0, 66.0, 195.0, 16.0),
    ],
)
def test_measurement_generalizes_to_scaled_variants(
    width: int,
    height: int,
    left_x: float,
    right_x: float,
    line_bottom: float,
    tri_h: float,
) -> None:
    known = ac0050_helpers.Ac0050Geometry(
        left_x=left_x,
        right_x=right_x,
        line_top=0.0,
        line_bottom=line_bottom,
        line_width=max(2.0, round(width * 0.03, 2)),
        triangle_half_base=max(5.0, round(width * 0.11, 2)),
        triangle_height=tri_h,
    )
    img = _synthetic_input(width, height, known)

    measured, _svg, _logs = ac0050_helpers.measureAndDrawAc0050Impl(img, cv2_module=cv2, np_module=np)

    assert abs(measured.left_x - known.left_x) <= max(2.0, width * 0.04)
    assert abs(measured.right_x - known.right_x) <= max(2.0, width * 0.04)
    assert measured.line_bottom >= known.line_bottom - max(4.0, height * 0.05)


def test_iterative_refinement_improves_projection_error() -> None:
    known = ac0050_helpers.Ac0050Geometry(
        left_x=6.0,
        right_x=34.0,
        line_top=0.0,
        line_bottom=130.0,
        line_width=2.0,
        triangle_half_base=5.0,
        triangle_height=10.0,
    )
    img = _synthetic_input(40, 140, known)
    start = ac0050_helpers.Ac0050Geometry(
        left_x=9.0,
        right_x=31.0,
        line_top=0.0,
        line_bottom=124.0,
        line_width=3.0,
        triangle_half_base=4.0,
        triangle_height=7.0,
    )

    refined, svg, logs = ac0050_helpers.refineAc0050GeometryIterativeImpl(
        img,
        start,
        cv2_module=cv2,
        np_module=np,
        rounds=4,
    )

    assert refined.left_x <= start.left_x
    assert refined.right_x >= start.right_x
    assert refined.line_bottom >= start.line_bottom
    assert "ac0050: iterative start_err=" in logs[0]
    assert "<svg" in svg


def test_iterative_refinement_can_optimize_colors() -> None:
    known = ac0050_helpers.Ac0050Geometry(
        left_x=6.0,
        right_x=34.0,
        line_top=0.0,
        line_bottom=130.0,
        line_width=2.0,
        triangle_half_base=5.0,
        triangle_height=10.0,
        left_line_color="#44aa22",
        right_line_color="#1155cc",
        left_triangle_color="#cc3344",
        right_triangle_color="#7733aa",
    )
    img = _synthetic_input(40, 140, known)

    start = ac0050_helpers.Ac0050Geometry(
        left_x=9.0,
        right_x=31.0,
        line_top=0.0,
        line_bottom=124.0,
        line_width=3.0,
        triangle_half_base=4.0,
        triangle_height=7.0,
        left_line_color="#111111",
        right_line_color="#111111",
        left_triangle_color="#111111",
        right_triangle_color="#111111",
    )

    refined, _svg, logs = ac0050_helpers.refineAc0050GeometryIterativeImpl(
        img,
        start,
        cv2_module=cv2,
        np_module=np,
        rounds=5,
        optimize_colors=True,
    )

    assert _hex_channel_distance(refined.left_line_color, known.left_line_color) <= 2
    assert _hex_channel_distance(refined.right_line_color, known.right_line_color) <= 2
    assert _hex_channel_distance(refined.left_triangle_color, known.left_triangle_color) <= 2
    assert _hex_channel_distance(refined.right_triangle_color, known.right_triangle_color) <= 2
    assert any("color left_line_color" in line for line in logs)
