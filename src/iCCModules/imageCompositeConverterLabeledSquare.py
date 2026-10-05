"""Register an explicitly labeled square and its lower stem from raster evidence."""
from __future__ import annotations

import copy
import math

import cv2
import numpy as np


def _hex(bgr):
    return '#' + ''.join(f'{int(round(v)):02x}' for v in bgr[::-1])


def fit_labeled_square(geometry_ir, *, image, render_fn, error_fn):
    """Fit observed geometry/colors while preserving the described text and topology.

    This deliberately handles one upright, filled square with a connected lower
    stem and a single contrast label. It does not identify text from image IDs,
    access reference vectors, or turn arbitrary raster contours into paths.
    """
    if (len(geometry_ir) != 1 or geometry_ir[0].get('kind') != 'UprightSquareKelleGlyph'
            or len(str(geometry_ir[0].get('label', ''))) != 1):
        return None
    arr = np.asarray(image)
    if arr.ndim != 3 or arr.shape[2] != 3 or min(arr.shape[:2]) < 8:
        return None
    height, width = arr.shape[:2]
    scale = min(width, height)
    mask = np.min(arr, axis=2) < 225
    spans = np.array([np.ptp(np.flatnonzero(row))+1 if row.any() else 0 for row in mask])
    rows = np.flatnonzero(spans >= max(spans.max()*.7, 5))
    if not len(rows) or not np.array_equal(rows, np.arange(rows[0], rows[-1]+1)):
        return None
    ys, xs = np.where(mask[rows[0]:rows[-1]+1])
    left, right, top, bottom = int(xs.min()), int(xs.max()+1), int(rows[0]), int(rows[-1]+1)
    bw, bh = right-left, bottom-top
    if not .75 <= bw/bh <= 1.3 or min(bw, bh) < 6:
        return None
    if np.mean(spans[rows] >= bw*.9) < .9:
        return None
    stem_y, stem_x = np.where(mask[bottom:])
    if not len(stem_y):
        return None
    stem_left, stem_right = int(stem_x.min()), int(stem_x.max()+1)
    stem_end = bottom+int(stem_y.max())+1
    stem_center = (stem_left+stem_right)/2
    if (stem_right-stem_left > bw*.3 or abs(stem_center-(left+right)/2) > bw*.1
            or stem_y.min() > 1 or not np.array_equal(np.unique(stem_y), np.arange(stem_y.max()+1))):
        return None
    crop = arr[top+2:bottom-2, left+2:right-2]
    if not crop.size:
        return None
    # Dominant interior color, then a connected contrast region for text bounds.
    buckets = (crop.reshape(-1, 3)//16).astype(int)
    colors, counts = np.unique(buckets, axis=0, return_counts=True)
    dominant = colors[int(np.argmax(counts))]
    body_color = np.median(crop[np.all(crop//16 == dominant, axis=2)], axis=0)
    contrast = np.linalg.norm(crop.astype(float)-body_color, axis=2) > 65
    count, labels, stats, _ = cv2.connectedComponentsWithStats(contrast.astype(np.uint8))
    if count < 2:
        return None
    interior_components = [i for i in range(1, count)
                           if stats[i, cv2.CC_STAT_LEFT] > 0 and stats[i, cv2.CC_STAT_TOP] > 0
                           and stats[i, cv2.CC_STAT_LEFT]+stats[i, cv2.CC_STAT_WIDTH] < crop.shape[1]
                           and stats[i, cv2.CC_STAT_TOP]+stats[i, cv2.CC_STAT_HEIGHT] < crop.shape[0]]
    if not interior_components:
        return None
    index = max(interior_components, key=lambda i: stats[i, cv2.CC_STAT_AREA])
    tx, ty, tw, th, area = map(int, stats[index])
    if (min(tw, th) < 2 or area < 4 or area > crop.shape[0]*crop.shape[1]*.6
            or tx == 0 or ty == 0 or tx+tw >= crop.shape[1] or ty+th >= crop.shape[0]):
        return None
    label_pixels = crop[labels == index]
    distances = np.linalg.norm(label_pixels.astype(float)-body_color, axis=1)
    label_color = np.median(label_pixels[distances >= np.percentile(distances, 75)], axis=0)
    border_color = np.median(np.concatenate((arr[top, left:right], arr[bottom-1, left:right],
                                            arr[top:bottom, left], arr[top:bottom, right-1])), axis=0)
    stem_color = np.median(arr[bottom:stem_end, int(stem_center)], axis=0)
    original = render_fn(geometry_ir)
    if original is None:
        return None
    initial_error = float(error_fn(original))
    element = copy.deepcopy(geometry_ir[0])
    element.update(body_bbox=[(left+.5)/width, (top+.5)/height, (bw-1)/width, (bh-1)/height],
                   body_fill=_hex(body_color), body_stroke=_hex(border_color), body_stroke_width=1/scale,
                   connector=[[stem_center/width, (bottom-.5)/height], [stem_center/width, stem_end/height]],
                   connector_width=(stem_right-stem_left)/scale, connector_stroke=_hex(stem_color),
                   label_fill=_hex(label_color), font_size=th/scale,
                   label_center=[(left+2+tx+tw/2)/width, (top+2+ty+th/2)/height])

    def measure(candidate):
        box = candidate['body_bbox']
        x, y, w, h = box[0]*width, box[1]*height, box[2]*width, box[3]*height
        cx, cy = candidate['label_center'][0]*width, candidate['label_center'][1]*height
        if not (w > 0 and h > 0 and .7 <= w/h <= 1.3 and x < cx < x+w and y < cy < y+h
                and 0 < candidate['body_stroke_width']*scale < min(w,h)*.2
                and 0 < candidate['connector_width']*scale < w*.3
                and 0 < candidate['font_size']*scale < h):
            return None
        candidate['connector'][0] = [candidate['connector'][1][0], (y+h)/height]
        if abs(candidate['connector'][0][0]*width-(x+w/2)) > w*.1:
            return None
        if candidate['connector'][1][1] <= candidate['connector'][0][1]:
            return None
        rendered = render_fn([candidate])
        if rendered is None:
            return None
        error = float(error_fn(rendered))
        return (error, copy.deepcopy(candidate), rendered) if math.isfinite(error) else None

    # Infer text placement using the production renderer's actual font metrics.
    observed = np.array([left+2+tx, top+2+ty, tw, th], float)
    best = None
    evaluations = 0
    for weight in ('400', '600', '700'):
        candidate = copy.deepcopy(element)
        candidate['font_weight'] = weight
        for _ in range(3):
            text = render_fn([candidate])
            blank = copy.deepcopy(candidate)
            blank.pop('label')
            background = render_fn([blank])
            if text is None or background is None:
                break
            gy, gx = np.where(np.max(np.abs(text.astype(float)-background.astype(float)), axis=2) > 50)
            if not len(gx):
                break
            glyph = np.array([gx.min(), gy.min(), gx.max()-gx.min()+1, gy.max()-gy.min()+1], float)
            candidate['label_center'][0] += (observed[0]+observed[2]/2-glyph[0]-glyph[2]/2)/width
            candidate['label_center'][1] += (observed[1]+observed[3]/2-glyph[1]-glyph[3]/2)/height
            candidate['font_size'] *= observed[3]/glyph[3]
        measured = measure(candidate)
        evaluations += 1
        if measured is not None and (best is None or measured[0] < best[0]):
            best = measured
    if best is None:
        return None
    # Bounded coarse-to-fine registration after topology and text bounds agree.
    for step in (1., .5, .25):
        for _ in range(2):
            changed = False
            for field, indices, divisor in (
                ('body_bbox', range(4), None), ('body_stroke_width', [None], scale),
                ('connector_width', [None], scale), ('label_center', range(2), None),
                ('font_size', [None], scale),
            ):
                for i in indices:
                    for direction in (-1, 1):
                        candidate = copy.deepcopy(best[1])
                        denominator = divisor or (width if i % 2 == 0 else height)
                        if i is None:
                            candidate[field] += direction*step/denominator
                        else:
                            candidate[field][i] += direction*step/denominator
                        measured = measure(candidate)
                        evaluations += 1
                        if measured is not None and measured[0] < best[0]-1e-9:
                            best, changed = measured, True
            if not changed:
                break
    if best[0] >= initial_error-1e-9:
        return None
    return {'geometry_ir': [best[1]], 'rendered': best[2], 'initial_error': initial_error,
            'final_error': best[0], 'evaluations': evaluations,
            'source': 'raster_labeled_square_registration_v1'}
