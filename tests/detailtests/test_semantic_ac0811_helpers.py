from __future__ import annotations

from src.iCCModules import imageCompositeConverterSemanticAc0811 as ac0811_helpers


class _ImgStub:
    shape = (45, 25, 3)


def _build_defaults() -> dict:
    return {
        "cx": 12.5,
        "cy": 17.0,
        "r": 11.0,
        "stroke_circle": 1.0,
        "stroke_gray": 127,
        "stem_width": 2.0,
        "stem_width_max": 2.5,
    }


def test_fit_ac0811_params_permanently_removes_locks() -> None:
    params = ac0811_helpers.fitAc0811ParamsFromImageImpl(
        _ImgStub(),
        _build_defaults(),
        fit_semantic_badge_from_image_fn=lambda _img, defaults: {
            **dict(defaults),
            "lock_circle_cx": True,
            "lock_circle_cy": True,
            "lock_stem_center_to_circle": True,
            "stem_len_min_ratio": 0.8,
        },
        estimate_upper_circle_from_foreground_fn=lambda _img, _defaults: None,
        clip_scalar_fn=lambda value, lo, hi: max(lo, min(hi, value)),
        normalize_light_circle_colors_fn=lambda p: p,
        persist_connector_length_floor_fn=lambda _params, _kind, default_ratio: None,
    )

    assert params["ac0811_no_restrictions"] is True
    assert params["lock_circle_cx"] is False
    assert params["lock_circle_cy"] is False
    assert params["lock_stem_center_to_circle"] is False
    assert params["stem_len_min_ratio"] == 0.0
