from __future__ import annotations

from pathlib import Path

import pytest

from src.iCCModules import imageCompositeConverterImageBackend as backend_helpers


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


class _FakeCv2:
    IMREAD_GRAYSCALE = 0

    def __init__(self, rows: list[list[int]] | None) -> None:
        self._rows = rows

    def imread(self, _path: str, _mode: int):
        if self._rows is None:
            return None

        class _FakeArray:
            def __init__(self, rows):
                self._rows = rows

            def tolist(self):
                return self._rows

        return _FakeArray(self._rows)


def test_pick_image_backend_prefers_opencv_when_available() -> None:
    backend = backend_helpers.pickImageBackendImpl(
        np_module=object(),
        cv2_module=_FakeCv2([[1, 2], [3, 4]]),
        import_with_vendored_fallback_fn=lambda _name: _FakeImageModule([[9]]),
    )

    assert backend.name == "opencv"
    assert backend.is_available() is True
    assert backend.load_grayscale(Path("dummy.png")) == [[1, 2], [3, 4]]


def test_pick_image_backend_falls_back_to_pure_python() -> None:
    backend = backend_helpers.pickImageBackendImpl(
        np_module=None,
        cv2_module=None,
        import_with_vendored_fallback_fn=lambda _name: _FakeImageModule([[5, 6], [7, 8]]),
    )

    assert backend.name == "pure_python"
    assert backend.is_available() is True
    assert backend.load_grayscale(Path("dummy.png")) == [[5, 6], [7, 8]]


def test_opencv_backend_raises_when_unavailable_or_missing_image() -> None:
    unavailable = backend_helpers.OpenCvImageBackend(np_module=None, cv2_module=None)
    with pytest.raises(RuntimeError, match="not available"):
        unavailable.load_grayscale(Path("missing.png"))

    missing = backend_helpers.OpenCvImageBackend(np_module=object(), cv2_module=_FakeCv2(None))
    with pytest.raises(FileNotFoundError, match="Could not read image"):
        missing.load_grayscale(Path("missing.png"))
