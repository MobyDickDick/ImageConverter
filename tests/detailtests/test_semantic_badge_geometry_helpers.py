from __future__ import annotations

from src.iCCModules import imageCompositeConverterSemanticBadgeGeometry as semantic_badge_geometry_helpers


def test_rotate_semantic_badge_clockwise_rotates_circle_and_arm_points() -> None:
    rotated = semantic_badge_geometry_helpers.rotateSemanticBadgeClockwiseImpl(
        {
            "cx": 8.0,
            "cy": 4.0,
            "arm_x1": 2.0,
            "arm_y1": 4.0,
            "arm_x2": 5.0,
            "arm_y2": 1.0,
        },
        w=20,
        h=10,
    )

    assert rotated["cx"] == 11.0
    assert rotated["cy"] == 3.0
    assert rotated["arm_x1"] == 11.0
    assert rotated["arm_y1"] == -3.0
    assert rotated["arm_x2"] == 14.0
    assert rotated["arm_y2"] == 0.0


def test_glyph_bbox_prefers_t_bounds_for_path_t_mode() -> None:
    bbox = semantic_badge_geometry_helpers.glyphBboxImpl(
        "path_t",
        t_xmin=1,
        t_ymin=2,
        t_xmax=3,
        t_ymax=4,
        m_xmin=5,
        m_ymin=6,
        m_xmax=7,
        m_ymax=8,
    )

    assert bbox == (1, 2, 3, 4)


def test_center_glyph_bbox_sets_tx_ty_for_centered_label() -> None:
    params = {"cx": 10.0, "cy": 6.0, "s": 2.0, "text_mode": "path"}

    semantic_badge_geometry_helpers.centerGlyphBboxImpl(
        params,
        glyph_bbox_fn=lambda _mode: (1, 2, 5, 6),
    )

    assert params["tx"] == 6.0
    assert params["ty"] == 2.0


def test_align_stem_to_circle_center_reanchors_stem_geometry() -> None:
    aligned = semantic_badge_geometry_helpers.alignStemToCircleCenterImpl(
        {
            "stem_enabled": True,
            "circle_enabled": True,
            "cx": 42.0,
            "cy": 38.0,
            "r": 9.0,
            "stem_width": 6.0,
        },
        default_stroke_width=4.0,
    )

    assert aligned["stem_x"] == 39.0
    assert aligned["stem_top"] == 43.7


def test_align_stem_to_circle_center_keeps_non_stem_badges_unchanged() -> None:
    params = {"stem_enabled": False, "cx": 10.0, "cy": 20.0, "r": 5.0}
    aligned = semantic_badge_geometry_helpers.alignStemToCircleCenterImpl(
        params,
        default_stroke_width=3.0,
    )

    assert aligned == params
