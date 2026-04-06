from __future__ import annotations

import numpy as np

from src.iCCModules import imageCompositeConverterCompositeSvg as composite_svg_helpers


class _FakeCv2Trace:
    TERM_CRITERIA_EPS = 2
    TERM_CRITERIA_MAX_ITER = 1
    KMEANS_RANDOM_CENTERS = 0
    RETR_CCOMP = 0
    CHAIN_APPROX_NONE = 1

    def kmeans(self, data, *_args, **_kwargs):
        labels = np.array([[0], [0], [0], [1]], dtype=np.int32)
        centers = np.array([[0, 0, 0], [255, 0, 0]], dtype=np.uint8)
        return None, labels, centers

    def inRange(self, _img, _low, _high):
        return np.array([[0, 255], [0, 255]], dtype=np.uint8)

    def findContours(self, _mask, _retr, _chain):
        contour = np.array([[[1, 2]], [[3, 4]], [[5, 6]]], dtype=np.int32)
        return [contour], None

    def contourArea(self, _contour):
        return 42.0

    def arcLength(self, _contour, _closed):
        return 10.0

    def approxPolyDP(self, contour, _epsilon, _closed):
        return contour


class _FakeCv2Composite:
    def __init__(self, img):
        self._img = img

    def imread(self, _path):
        return self._img


def test_trace_image_segment_impl_returns_svg_paths():
    img = np.zeros((2, 2, 3), dtype=np.uint8)
    paths = composite_svg_helpers.traceImageSegmentImpl(
        img,
        0.2,
        scale_x=2.0,
        scale_y=3.0,
        offset_x=1.0,
        offset_y=2.0,
        cv2_module=_FakeCv2Trace(),
        np_module=np,
        rgb_to_hex_fn=lambda _rgb: "#112233",
    )

    assert len(paths) == 1
    assert '#112233' in paths[0]
    assert '3.000,8.000' in paths[0]


def test_generate_composite_svg_impl_uses_top_ref_and_square_cross(tmp_path):
    ref = tmp_path / 'SRC.jpg'
    ref.write_bytes(b'noop')
    ref_img = np.zeros((10, 20, 3), dtype=np.uint8)

    calls: list[tuple[tuple[int, ...], float, float]] = []

    def _trace(img_segment, epsilon, *, scale_x, scale_y):
        calls.append((img_segment.shape, scale_x, scale_y))
        assert epsilon == 0.5
        return ['  <path d="M 0,0 Z" fill="#000" stroke="none" />']

    svg = composite_svg_helpers.generateCompositeSvgImpl(
        40,
        20,
        {'top_source_ref': 'SRC', 'bottom_shape': 'square_cross'},
        str(tmp_path),
        0.5,
        os_module=__import__('os'),
        cv2_module=_FakeCv2Composite(ref_img),
        trace_image_segment_fn=_trace,
    )

    assert len(calls) == 1
    assert calls[0][0] == (6, 20, 3)
    assert calls[0][1] == 2.0
    assert 'rect' in svg
    assert svg.endswith('</svg>')
