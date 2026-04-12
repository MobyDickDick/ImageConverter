from __future__ import annotations

import pytest

from src.iCCModules import imageCompositeConverterColorUtils as color_utils_helpers


class _FakeNp:
    @staticmethod
    def clip(value, low, high):
        return ("clipped", value, low, high)


def test_clip_impl_uses_numpy_when_available() -> None:
    clipped = color_utils_helpers.clipImpl(10, 1, 5, np_module=_FakeNp(), clip_scalar_fn=lambda *_args: -1)
    assert clipped == ("clipped", 10, 1, 5)


def test_clip_impl_uses_scalar_fallback_without_numpy() -> None:
    clipped = color_utils_helpers.clipImpl(10, 1, 5, np_module=None, clip_scalar_fn=lambda value, low, high: min(high, max(low, value)))
    assert clipped == 5


def test_clip_impl_raises_for_non_scalar_without_numpy() -> None:
    with pytest.raises(RuntimeError):
        color_utils_helpers.clipImpl([1, 2], 0, 1, np_module=None, clip_scalar_fn=lambda *_args: 0)


def test_gray_to_hex_impl_clamps_and_rounds() -> None:
    assert color_utils_helpers.grayToHexImpl(128.4) == "#808080"
    assert color_utils_helpers.grayToHexImpl(-10.0) == "#000000"
    assert color_utils_helpers.grayToHexImpl(999.0) == "#ffffff"


def test_rgb_to_hex_impl_formats_channels() -> None:
    assert color_utils_helpers.rgbToHexImpl([16, 32, 255]) == "#1020ff"
