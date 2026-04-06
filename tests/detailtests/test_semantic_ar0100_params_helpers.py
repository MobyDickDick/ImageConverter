from __future__ import annotations

from src.iCCModules import imageCompositeConverterSemanticAr0100 as ar0100_helpers


def test_build_ar0100_badge_params_scales_geometry_and_centers_glyph_bbox() -> None:
    base = {
        "cx": 10.0,
        "cy": 11.0,
        "r": 4.0,
        "stroke_width": 1.5,
        "fill_gray": 220,
        "stroke_gray": 150,
        "text_gray": 120,
        "tx": 9.0,
        "ty": 8.0,
        "s": 0.5,
    }
    centered = {"called": False}

    def _center(params: dict) -> None:
        centered["called"] = True
        params["bbox_centered"] = True

    params = ar0100_helpers.buildAr0100BadgeParamsImpl(
        50,
        25,
        ar0100_base=base,
        center_glyph_bbox_fn=_center,
    )

    assert centered["called"] is True
    assert params["bbox_centered"] is True
    assert params["cx"] == 10.0
    assert params["cy"] == 11.0
    assert params["r"] == 4.0
    assert params["stroke_circle"] == 1.5
    assert params["label"] == "M"
    assert params["text_mode"] == "path"
