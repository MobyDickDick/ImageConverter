"""Infer a simple bar-and-stem interior mark from contrast and occupancy."""
from __future__ import annotations

import copy

import cv2
import numpy as np


def fit_rectilinear_interior_mark(geometry_ir, *, image, description, render_fn, error_fn):
    """Keep an eight-corner mark only when raster topology and render fit agree.

    This is a geometric observation, not OCR. It does not assert a letter or
    import outlines, sample vectors, dimensions, or colors from another case.
    """
    if len(geometry_ir) != 1 or geometry_ir[0].get('kind') != 'MainDiagonalMirroredSquareKelleGlyph':
        return None
    if any(word in description.casefold() for word in ('ohne text', 'ohne beschriftung', 'ohne markierung', 'ohne buchstabe', 'kein buchstabe')):
        return None
    arr = np.asarray(image)
    if arr.ndim != 3 or arr.shape[2] != 3 or arr.size == 0:
        return None
    height, width = arr.shape[:2]
    bx, by, bw, bh = geometry_ir[0]['body_bbox']
    x0, y0 = int(np.ceil(bx*width+1)), int(np.ceil(by*height+1))
    x1, y1 = int(np.floor((bx+bw)*width-1)), int(np.floor((by+bh)*height-1))
    if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
        return None
    crop = arr[y0:y1, x0:x1].astype(float)
    luminance = crop.mean(axis=2)
    low, high = np.percentile(luminance, [25, 95])
    if high-low < 45:
        return None
    # Strong contrast cores avoid treating JPEG/antialiasing fringes as bars.
    mask = (luminance > low+.7*(high-low)).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    if count < 2:
        return None
    index = 1+int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    x, y, w, h, area = map(int, stats[index])
    if min(w, h) < 3 or area < 5 or x == 0 or y == 0 or x+w >= crop.shape[1] or y+h >= crop.shape[0]:
        return None
    region = labels[y:y+h, x:x+w] == index
    spans = region.sum(axis=1)
    bar_rows = np.flatnonzero(spans >= w*.8)
    if not len(bar_rows) or bar_rows[0] != 0:
        return None
    bar_height = int(bar_rows[-1])+1
    if bar_height >= h*.6 or not np.array_equal(bar_rows, np.arange(bar_height)):
        return None
    stem_columns = np.flatnonzero(region[bar_height:].mean(axis=0) >= .8)
    if not len(stem_columns) or not np.array_equal(stem_columns, np.arange(stem_columns[0], stem_columns[-1]+1)):
        return None
    left, right = int(stem_columns[0]), int(stem_columns[-1])+1
    if right-left >= w*.7 or abs((left+right)/2-w/2) > w*.2:
        return None
    expected = np.zeros_like(region)
    expected[:bar_height] = True
    expected[bar_height:, left:right] = True
    if (region & expected).sum()/(region | expected).sum() < .85:
        return None
    color = np.median(crop[labels == index], axis=0)
    parameters = [float(x0+x), float(y0+y), float(w), float(h),
                  float(bar_height), float(left), float(right)]

    def candidate(values):
        px, py, pw, ph, bar, sl, sr = values
        if not (0 < bar < ph and 0 < sl < sr < pw
                and x0 <= px < px+pw <= x1 and y0 <= py < py+ph <= y1):
            return None
        points = [(px, py), (px+pw, py), (px+pw, py+bar), (px+sr, py+bar),
                  (px+sr, py+ph), (px+sl, py+ph), (px+sl, py+bar), (px, py+bar)]
        mark = {'kind': 'PolygonPath', 'id': 'raster_interior_mark', 'role': 'observed_interior_mark',
                'points': [[qx/width, qy/height] for qx, qy in points], 'closed': True,
                'fill': '#'+''.join(f'{int(round(v)):02x}' for v in color[::-1]),
                'stroke': 'none', 'stroke_width': 0., 'source': 'raster_bar_and_stem_occupancy_v1'}
        ir = [*copy.deepcopy(geometry_ir), mark]
        rendered = render_fn(ir)
        return None if rendered is None else (float(error_fn(rendered)), ir, rendered)

    base = render_fn(geometry_ir)
    if base is None:
        return None
    initial_error = float(error_fn(base))
    best = candidate(parameters)
    if best is None:
        return None
    # Resolve observed bars first; only then register their measured boundaries.
    for step in (1., .5):
        for index in range(len(parameters)):
            for direction in (-1., 1.):
                probe = parameters.copy()
                probe[index] += direction*step
                measured = candidate(probe)
                if measured is not None and measured[0] < best[0]-1e-9:
                    parameters, best = probe, measured
    if best[0] >= initial_error-1e-9:
        return None
    return {'geometry_ir': best[1], 'rendered': best[2], 'initial_error': initial_error,
            'final_error': best[0], 'source': 'raster_bar_and_stem_occupancy_v1'}
