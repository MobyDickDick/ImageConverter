from __future__ import annotations

import numpy as np

from src.iCCModules import imageCompositeConverterElementMasks as element_mask_helpers


class _Cv2Stub:
    @staticmethod
    def dilate(_img, _kernel, iterations=1):
        raise AssertionError("dilate should not run in this test")


def test_extract_badge_element_mask_returns_none_for_missing_region() -> None:
    img = np.zeros((6, 6, 3), dtype=np.uint8)

    result = element_mask_helpers.extractBadgeElementMaskImpl(
        img,
        {},
        "circle",
        element_region_mask_fn=lambda *_args, **_kwargs: None,
        foreground_mask_fn=lambda _img: np.ones((6, 6), dtype=bool),
        cv2_module=_Cv2Stub,
        np_module=np,
    )

    assert result is None


def test_extract_badge_element_mask_intersects_region_and_foreground() -> None:
    img = np.zeros((6, 6, 3), dtype=np.uint8)
    region = np.zeros((6, 6), dtype=bool)
    region[1:5, 1:5] = True
    foreground = np.zeros((6, 6), dtype=bool)
    foreground[2:4, 2:4] = True

    result = element_mask_helpers.extractBadgeElementMaskImpl(
        img,
        {"validation_mask_dilate_px": 0},
        "circle",
        element_region_mask_fn=lambda *_args, **_kwargs: region,
        foreground_mask_fn=lambda _img: foreground,
        cv2_module=_Cv2Stub,
        np_module=np,
    )

    assert result is not None
    assert bool(np.array_equal(result, foreground))
