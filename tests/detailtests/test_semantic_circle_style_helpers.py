from __future__ import annotations

import numpy as np

from src.iCCModules import imageCompositeConverterSemanticCircleStyle as semantic_circle_style_helpers


def test_normalize_light_circle_colors_updates_expected_fields() -> None:
    params = {"stem_enabled": True, "draw_text": True, "text_gray": 10}
    normalized = semantic_circle_style_helpers.normalizeLightCircleColorsImpl(
        params,
        light_circle_fill_gray=240,
        light_circle_stroke_gray=120,
        light_circle_text_gray=110,
    )

    assert normalized["fill_gray"] == 240
    assert normalized["stroke_gray"] == 120
    assert normalized["stem_gray"] == 120
    assert normalized["text_gray"] == 110


def test_normalize_ac08_line_widths_preserves_outer_diameter_when_requested() -> None:
    normalized = semantic_circle_style_helpers.normalizeAc08LineWidthsImpl(
        {
            "circle_enabled": True,
            "r": 8.0,
            "stroke_circle": 3.0,
            "preserve_outer_diameter_on_stroke_normalization": True,
            "stem_enabled": True,
            "arm_enabled": True,
            "cx": 10.0,
            "stroke_gray": 127,
        },
        ac08_stroke_width_px=1.0,
        light_circle_stroke_gray=127,
    )

    assert normalized["stroke_circle"] == 1.0
    assert normalized["r"] == 9.0
    assert normalized["lock_stroke_widths"] is True
    assert normalized["arm_stroke"] == 1.0
    assert normalized["stem_width"] == 1.0
    assert normalized["stem_x"] == 9.5
    assert normalized["stem_gray"] == 127


def test_estimate_border_background_gray_uses_image_border_median() -> None:
    gray = np.array(
        [
            [10, 10, 10],
            [10, 200, 10],
            [10, 10, 10],
        ],
        dtype=np.uint8,
    )

    assert semantic_circle_style_helpers.estimateBorderBackgroundGrayImpl(gray, np_module=np) == 10.0


def test_estimate_circle_tones_and_stroke_returns_stable_ranges() -> None:
    gray = np.full((21, 21), 220, dtype=np.uint8)
    yy, xx = np.indices(gray.shape)
    dist = np.sqrt((xx - 10.0) ** 2 + (yy - 10.0) ** 2)
    ring = np.abs(dist - 6.0) <= 1.0
    gray[dist <= 4.0] = 200
    gray[ring] = 80

    fill_gray, ring_gray, stroke_est = semantic_circle_style_helpers.estimateCircleTonesAndStrokeImpl(
        gray,
        cx=10.0,
        cy=10.0,
        r=6.0,
        stroke_hint=1.0,
        np_module=np,
    )

    assert fill_gray <= 205.0
    assert ring_gray <= 100.0
    assert 1.0 <= stroke_est <= 6.0
