from __future__ import annotations

from src.iCCModules import imageCompositeConverterMaskMetrics as helpers


def test_iou_impl_returns_overlap_ratio() -> None:
    a = [
        [1, 0, 0],
        [1, 1, 0],
    ]
    b = [
        [1, 1, 0],
        [0, 1, 0],
    ]

    score = helpers.iouImpl(a, b)

    assert score == 0.5
