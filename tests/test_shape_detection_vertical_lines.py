from __future__ import annotations

import pytest

np = pytest.importorskip("numpy")
cv2 = pytest.importorskip("cv2")

from tools.shape_detection import detect_vertical_lines


def test_detect_vertical_lines_finds_single_vertical_stroke() -> None:
    image = np.zeros((120, 120), dtype=np.uint8)
    cv2.line(image, (60, 20), (60, 100), 255, 4)
    detections = detect_vertical_lines(image)
    assert detections
    top = detections[0]
    assert abs(top.x_center - 60) <= 3
    assert top.length_px >= 70


def test_detect_vertical_lines_rejects_horizontal_line() -> None:
    image = np.zeros((120, 120), dtype=np.uint8)
    cv2.line(image, (20, 60), (100, 60), 255, 4)
    assert detect_vertical_lines(image) == []
