from __future__ import annotations

import src.imageCompositeConverter as converter
from src.iCCModules import imageCompositeConverterRemaining as helpers

np = converter._importWithVendoredFallback("numpy")


def test_looks_like_elongated_foreground_rect_detects_wide_bar() -> None:
    assert np is not None
    img = np.full((24, 120, 3), 255, dtype=np.uint8)
    img[8:14, 10:110] = np.array([180, 180, 180], dtype=np.uint8)

    assert helpers._looksLikeElongatedForegroundRect(img) is True


def test_looks_like_elongated_foreground_rect_rejects_compact_blob() -> None:
    assert np is not None
    img = np.full((40, 40, 3), 255, dtype=np.uint8)
    img[10:30, 10:30] = np.array([160, 160, 160], dtype=np.uint8)

    assert helpers._looksLikeElongatedForegroundRect(img) is False
