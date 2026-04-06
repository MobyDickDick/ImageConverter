from __future__ import annotations

import numpy as np

from src.iCCModules import imageCompositeConverterDiffing as diffing_helpers


class _FakeCv2:
    INTER_AREA = 0
    INTER_NEAREST = 1

    @staticmethod
    def resize(img: np.ndarray, shape: tuple[int, int], interpolation: int = 0) -> np.ndarray:
        width, height = shape
        return img[:height, :width].copy()

    @staticmethod
    def absdiff(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return np.abs(a.astype(np.int16) - b.astype(np.int16)).astype(np.uint8)


def test_calculate_error_impl_returns_inf_for_missing_svg() -> None:
    img = np.zeros((2, 2, 3), dtype=np.uint8)

    err = diffing_helpers.calculateErrorImpl(img, None, cv2_module=_FakeCv2, np_module=np)

    assert np.isinf(err)


def test_calculate_error_impl_uses_mean_absdiff() -> None:
    img_orig = np.zeros((2, 2, 3), dtype=np.uint8)
    img_svg = np.zeros((2, 2, 3), dtype=np.uint8)
    img_svg[0, 0, :] = [30, 0, 0]

    err = diffing_helpers.calculateErrorImpl(img_orig, img_svg, cv2_module=_FakeCv2, np_module=np)

    assert err == 2.5


def test_create_diff_image_impl_applies_focus_mask() -> None:
    img_orig = np.full((2, 2, 3), 80, dtype=np.uint8)
    img_svg = np.full((2, 2, 3), 100, dtype=np.uint8)
    focus_mask = np.array([[1, 0], [0, 0]], dtype=np.uint8)

    diff = diffing_helpers.createDiffImageImpl(
        img_orig,
        img_svg,
        cv2_module=_FakeCv2,
        np_module=np,
        focus_mask=focus_mask,
    )

    assert np.any(diff[0, 0] != 0)
    assert np.all(diff[0, 1] == 0)
    assert np.all(diff[1, 0] == 0)
    assert np.all(diff[1, 1] == 0)
