from __future__ import annotations

from src import imageCompositeConverter as icc
from src.iCCModules import imageCompositeConverterOptimizationElementAlignment as helpers


def _clip(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def test_estimate_vertical_stem_from_mask_returns_center_and_width() -> None:
    mask = icc.np.zeros((20, 20), dtype=bool)
    mask[6:18, 8:12] = True

    est = helpers.estimateVerticalStemFromMaskImpl(
        mask,
        expected_cx=10.0,
        y_start=0,
        y_end=20,
        np_module=icc.np,
    )

    assert est is not None
    est_cx, est_width = est
    assert abs(est_cx - 9.5) < 0.6
    assert abs(est_width - 4.0) < 0.6


def test_apply_element_alignment_step_updates_stem_geometry() -> None:
    params = {
        "stem_enabled": True,
        "stem_x": 12.0,
        "stem_width": 4.0,
        "stem_top": 8.0,
        "stem_bottom": 26.0,
        "lock_stem_center_to_circle": False,
    }

    changed = helpers.applyElementAlignmentStepImpl(
        params,
        "stem",
        center_dx=2.0,
        center_dy=1.0,
        diag_scale=1.1,
        w=60,
        h=60,
        clip_scalar_fn=_clip,
    )

    assert changed is True
    assert params["stem_width"] > 4.0
    assert params["stem_x"] != 12.0
