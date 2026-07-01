from __future__ import annotations

import numpy as np

from src.iCCModules import imageCompositeConverterDiffing as diffing_helpers


class _FakeCv2:
    INTER_AREA = 0
    INTER_NEAREST = 1

    @staticmethod
    def resize(
        img: np.ndarray, shape: tuple[int, int], interpolation: int = 0
    ) -> np.ndarray:
        width, height = shape
        return img[:height, :width].copy()

    @staticmethod
    def absdiff(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return np.abs(a.astype(np.int16) - b.astype(np.int16)).astype(np.uint8)


def test_calculate_error_impl_returns_inf_for_missing_svg() -> None:
    img = np.zeros((2, 2, 3), dtype=np.uint8)

    err = diffing_helpers.calculateErrorImpl(
        img, None, cv2_module=_FakeCv2, np_module=np
    )

    assert np.isinf(err)


def test_calculate_error_impl_uses_mean_absdiff() -> None:
    img_orig = np.zeros((2, 2, 3), dtype=np.uint8)
    img_svg = np.zeros((2, 2, 3), dtype=np.uint8)
    img_svg[0, 0, :] = [30, 0, 0]

    err = diffing_helpers.calculateErrorImpl(
        img_orig, img_svg, cv2_module=_FakeCv2, np_module=np
    )

    assert err == 2.5


def test_create_diff_image_impl_marks_ranked_delta2_pixels_black() -> None:
    img_orig = np.full((2, 2, 3), 80, dtype=np.uint8)
    img_svg = img_orig.copy()
    img_svg[0, 0] = [100, 100, 100]
    img_svg[1, 1] = [80, 90, 80]

    diff = diffing_helpers.createDiffImageImpl(
        img_orig,
        img_svg,
        cv2_module=_FakeCv2,
        np_module=np,
    )

    assert np.all(diff[0, 0] == 0)
    assert np.all(diff[1, 1] == 0)
    assert np.all(diff[0, 1] == img_orig[0, 1])
    assert np.all(diff[1, 0] == img_orig[1, 0])


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

    assert np.all(diff[0, 0] == 0)
    assert np.all(diff[0, 1] == img_orig[0, 1])
    assert np.all(diff[1, 0] == img_orig[1, 0])
    assert np.all(diff[1, 1] == img_orig[1, 1])


class _CommentCv2(_FakeCv2):
    FONT_HERSHEY_SIMPLEX = 0
    LINE_AA = 8

    @staticmethod
    def putText(img, text, org, font, scale, color, thickness, line_type):
        # Mark the requested text origin so tests can verify that the comment
        # panel is not blank without depending on OpenCV font rasterization.
        x, y = org
        img[max(0, y - 1) : y + 1, min(x, img.shape[1] - 1) : img.shape[1]] = 0
        return img


def test_diff_pixel_summary_reports_changed_pixels_and_extrema() -> None:
    img_orig = np.zeros((2, 2, 3), dtype=np.uint8)
    img_svg = img_orig.copy()
    img_svg[1, 0] = [10, 20, 30]

    summary = diffing_helpers.diffPixelSummaryImpl(
        img_orig,
        img_svg,
        cv2_module=_FakeCv2,
        np_module=np,
    )

    assert summary["changed_pixels"] == 1
    assert summary["pixel_count"] == 4
    assert summary["changed_bbox"] == (0, 1, 0, 1)
    assert summary["max_delta_position"] == (0, 1)
    assert summary["max_abs_channel_delta"] == 30


def test_create_commented_diff_image_appends_description_panel() -> None:
    diff = np.zeros((2, 3, 3), dtype=np.uint8)
    summary = {"pixel_count": 6, "changed_pixels": 2, "changed_fraction": 2 / 6}

    commented = diffing_helpers.createCommentedDiffImageImpl(
        diff,
        summary,
        cv2_module=_CommentCv2,
        np_module=np,
        title="AC0001: source vs render",
    )

    assert commented.shape == (150, 640, 3)
    assert np.any(commented[2:] != 255)
