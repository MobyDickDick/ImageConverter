from __future__ import annotations

from pathlib import Path

import pytest

from src.iCCModules import imageCompositeConverterImageLoading as image_loading_helpers


class _FakeGrayImage:
    def __init__(self, rows: list[list[int]]) -> None:
        self._rows = rows
        self.size = (len(rows[0]), len(rows))

    def convert(self, _mode: str):
        return self

    def load(self):
        return self

    def __getitem__(self, xy: tuple[int, int]) -> int:
        x, y = xy
        return self._rows[y][x]


class _FakeImageModule:
    def __init__(self, rows: list[list[int]]) -> None:
        self._rows = rows

    def open(self, _path: Path) -> _FakeGrayImage:
        return _FakeGrayImage(self._rows)


def test_load_grayscale_image_impl_reads_pixels() -> None:
    def _import(_name: str):
        return _FakeImageModule([[5, 6], [7, 8]])

    loaded = image_loading_helpers.loadGrayscaleImageImpl(
        Path("dummy.png"),
        import_with_vendored_fallback_fn=_import,
    )

    assert loaded == [[5, 6], [7, 8]]


def test_load_binary_image_with_mode_impl_global_and_otsu() -> None:
    grayscale = [[10, 200], [221, 0]]

    global_binary = image_loading_helpers.loadBinaryImageWithModeImpl(
        Path("dummy.png"),
        threshold=220,
        mode="global",
        load_grayscale_image_fn=lambda _path: grayscale,
        compute_otsu_threshold_fn=lambda _gray: 100,
        adaptive_threshold_fn=lambda _gray: [[0]],
    )
    assert global_binary == [[1, 1], [0, 1]]

    otsu_binary = image_loading_helpers.loadBinaryImageWithModeImpl(
        Path("dummy.png"),
        mode="otsu",
        load_grayscale_image_fn=lambda _path: grayscale,
        compute_otsu_threshold_fn=lambda _gray: 100,
        adaptive_threshold_fn=lambda _gray: [[0]],
    )
    assert otsu_binary == [[1, 0], [0, 1]]


def test_load_binary_image_with_mode_impl_adaptive_and_invalid_mode() -> None:
    adaptive_binary = image_loading_helpers.loadBinaryImageWithModeImpl(
        Path("dummy.png"),
        mode="adaptive",
        load_grayscale_image_fn=lambda _path: [[1]],
        compute_otsu_threshold_fn=lambda _gray: 0,
        adaptive_threshold_fn=lambda _gray: [[1, 0], [0, 1]],
    )
    assert adaptive_binary == [[1, 0], [0, 1]]

    with pytest.raises(ValueError, match="Unknown threshold mode"):
        image_loading_helpers.loadBinaryImageWithModeImpl(
            Path("dummy.png"),
            mode="invalid",
            load_grayscale_image_fn=lambda _path: [[1]],
            compute_otsu_threshold_fn=lambda _gray: 0,
            adaptive_threshold_fn=lambda _gray: [[1]],
        )
