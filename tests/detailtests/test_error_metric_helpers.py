from __future__ import annotations

import numpy as np

from src.iCCModules import imageCompositeConverterElementErrorMetrics as error_metric_helpers


class _FakeCv2:
    COLOR_BGR2GRAY = 1
    INTER_AREA = 0

    @staticmethod
    def resize(img: np.ndarray, shape: tuple[int, int], interpolation: int = 0) -> np.ndarray:
        return img

    @staticmethod
    def absdiff(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return np.abs(a.astype(np.int16) - b.astype(np.int16)).astype(np.uint8)

    @staticmethod
    def cvtColor(img: np.ndarray, code: int) -> np.ndarray:
        return img.mean(axis=2).astype(np.uint8)


def _mask_bbox(mask: np.ndarray) -> tuple[float, float, float, float] | None:
    ys, xs = np.where(mask)
    if xs.size == 0:
        return None
    return float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max())


def test_element_only_params_impl() -> None:
    params = {"draw_text": True, "stem_enabled": True, "arm_enabled": True}

    circle = error_metric_helpers.elementOnlyParamsImpl(params, "circle")
    text = error_metric_helpers.elementOnlyParamsImpl(params, "text")

    assert circle["circle_enabled"] is True
    assert circle["draw_text"] is False
    assert text["draw_text"] is True
    assert text["stem_enabled"] is False


def test_union_bbox_from_masks_impl_combines_boxes() -> None:
    mask_a = np.zeros((5, 5), dtype=bool)
    mask_a[1:3, 1:3] = True
    mask_b = np.zeros((5, 5), dtype=bool)
    mask_b[2:5, 3:5] = True

    bbox = error_metric_helpers.unionBboxFromMasksImpl(mask_a, mask_b, mask_bbox_fn=_mask_bbox, np_module=np)

    assert bbox == (1, 1, 4, 4)


def test_masked_union_error_in_bbox_impl_returns_finite_value() -> None:
    img_orig = np.zeros((4, 4, 3), dtype=np.uint8)
    img_svg = np.zeros((4, 4, 3), dtype=np.uint8)
    img_svg[1:3, 1:3, :] = 50
    mask_orig = np.zeros((4, 4), dtype=bool)
    mask_svg = np.zeros((4, 4), dtype=bool)
    mask_orig[1:3, 1:3] = True
    mask_svg[1:3, 1:3] = True

    err = error_metric_helpers.maskedUnionErrorInBboxImpl(
        img_orig,
        img_svg,
        mask_orig,
        mask_svg,
        cv2_module=_FakeCv2,
        np_module=np,
        union_bbox_from_masks_fn=lambda a, b: error_metric_helpers.unionBboxFromMasksImpl(
            a,
            b,
            mask_bbox_fn=_mask_bbox,
            np_module=np,
        ),
    )

    assert err > 0.0


def test_masked_error_impl_handles_empty_mask() -> None:
    img = np.zeros((3, 3, 3), dtype=np.uint8)
    mask = np.zeros((3, 3), dtype=bool)

    err = error_metric_helpers.maskedErrorImpl(img, img, mask, cv2_module=_FakeCv2, np_module=np)

    assert np.isinf(err)


def test_calculate_delta2_stats_impl_returns_mean_and_std() -> None:
    img_orig = np.zeros((2, 2, 3), dtype=np.uint8)
    img_svg = np.zeros((2, 2, 3), dtype=np.uint8)
    img_svg[0, 0, :] = [1, 2, 3]

    mean_delta2, std_delta2 = error_metric_helpers.calculateDelta2StatsImpl(
        img_orig,
        img_svg,
        cv2_module=_FakeCv2,
        np_module=np,
    )

    # delta2 values per pixel: [14, 0, 0, 0]
    assert mean_delta2 == 3.5
    assert std_delta2 > 0.0


def test_element_match_error_impl_penalizes_undersized_circle() -> None:
    img_orig = np.zeros((10, 10, 3), dtype=np.uint8)
    img_svg = np.zeros((10, 10, 3), dtype=np.uint8)
    mask_orig = np.zeros((10, 10), dtype=bool)
    mask_svg = np.zeros((10, 10), dtype=bool)
    mask_orig[2:8, 2:8] = True
    mask_svg[3:7, 3:7] = True

    err = error_metric_helpers.elementMatchErrorImpl(
        img_orig,
        img_svg,
        params={},
        element="circle",
        mask_orig=mask_orig,
        mask_svg=mask_svg,
        cv2_module=_FakeCv2,
        np_module=np,
        extract_badge_element_mask_fn=lambda *_args, **_kwargs: None,
        masked_union_error_in_bbox_fn=lambda *_args, **_kwargs: 0.0,
        mask_centroid_radius_fn=lambda m: (5.0, 5.0, 3.0) if int(m.sum()) > 20 else (5.0, 5.0, 2.0),
    )

    assert err > 0.0
