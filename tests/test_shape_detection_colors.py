from __future__ import annotations

import pytest

np = pytest.importorskip("numpy")
cv2 = pytest.importorskip("cv2")

from tools.shape_detection import detect_primitive_colors


def test_detect_primitive_colors_returns_fill_and_stroke() -> None:
    image = np.full((80, 80, 3), 255, dtype=np.uint8)
    cv2.rectangle(image, (10, 10), (70, 70), (255, 0, 0), thickness=-1)  # blue in BGR
    cv2.rectangle(image, (10, 10), (70, 70), (0, 0, 255), thickness=4)  # red in BGR

    fill_mask = np.zeros((80, 80), dtype=np.uint8)
    fill_mask[16:65, 16:65] = 255
    stroke_mask = np.zeros((80, 80), dtype=np.uint8)
    cv2.rectangle(stroke_mask, (10, 10), (70, 70), 255, thickness=4)

    result = detect_primitive_colors(image, fill_mask=fill_mask, stroke_mask=stroke_mask)
    assert result.fill_rgb == (0, 0, 255)
    assert result.stroke_rgb == (255, 0, 0)
    assert result.fill_hex == "#0000FF"
    assert result.stroke_hex == "#FF0000"
