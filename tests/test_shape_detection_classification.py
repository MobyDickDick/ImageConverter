from __future__ import annotations

import pytest

np = pytest.importorskip("numpy")
cv2 = pytest.importorskip("cv2")

from tools.shape_detection import classify_contour_shape


def _largest_contour(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    assert contours
    return max(contours, key=cv2.contourArea)


def test_classify_triangle() -> None:
    mask = np.zeros((120, 120), dtype=np.uint8)
    pts = np.array([[60, 15], [20, 100], [100, 100]], dtype=np.int32)
    cv2.fillPoly(mask, [pts], 255)
    shape = classify_contour_shape(_largest_contour(mask))
    assert shape.primitive == "triangle"


def test_classify_rectangle() -> None:
    mask = np.zeros((120, 120), dtype=np.uint8)
    cv2.rectangle(mask, (20, 30), (100, 90), 255, thickness=-1)
    shape = classify_contour_shape(_largest_contour(mask))
    assert shape.primitive == "rectangle"


def test_classify_arrow_non_convex() -> None:
    mask = np.zeros((160, 160), dtype=np.uint8)
    pts = np.array([
        [20, 70], [90, 70], [90, 45], [145, 80], [90, 115], [90, 90], [20, 90]
    ], dtype=np.int32)
    cv2.fillPoly(mask, [pts], 255)
    shape = classify_contour_shape(_largest_contour(mask))
    assert shape.primitive == "arrow"
    assert not shape.is_convex
