"""Register an explicitly labeled square and its stem from raster evidence."""
from __future__ import annotations

import copy
import math

import cv2
import numpy as np


def _hex(bgr):
    return '#' + ''.join(f'{int(round(v)):02x}' for v in bgr[::-1])


def _contour_metrics(reference, rendered):
    """Compare residual, contour and foreground evidence for local refinement."""
    a = cv2.Canny(reference.astype(np.uint8), 50, 140) > 0
    b = cv2.Canny(rendered.astype(np.uint8), 50, 140) > 0
    if not a.any() or not b.any():
        edge = 0.
    else:
        da = cv2.distanceTransform((~a).astype(np.uint8), cv2.DIST_L2, 3)
        db = cv2.distanceTransform((~b).astype(np.uint8), cv2.DIST_L2, 3)
        edge = float((np.exp(-db[a]).mean()+np.exp(-da[b]).mean())/2)
    # Use background-relative foreground evidence for colored antialiasing:
    # a fixed brightness cutoff can mistake changed contour coverage for a
    # lost object, even when its contrast silhouette is unchanged.
    border = np.concatenate((reference[0], reference[-1], reference[:, 0], reference[:, -1]))
    background = np.median(border.astype(float), axis=0)
    ma = np.max(np.abs(reference.astype(float)-background), axis=2) > 25
    mb = np.max(np.abs(rendered.astype(float)-background), axis=2) > 25
    union = (ma | mb).sum()
    iou = float((ma & mb).sum()/union) if union else 1.
    residual = float(np.mean(np.sum((reference.astype(float)-rendered.astype(float))**2, axis=2)))
    return residual, edge, iou


def _fit_right_stem_labeled_square(geometry_ir, *, image, render_fn, error_fn, _squared_contour=False):
    """Transpose the body/handle fit while rendering text in its original axes."""
    original = geometry_ir[0]

    def transpose(element, kind):
        result = copy.deepcopy(element)
        x, y, w, h = result['body_bbox']
        result.update(kind=kind, body_bbox=[y, x, h, w],
                      connector=[[v, u] for u, v in result['connector']])
        if 'label_center' in result:
            result['label_center'] = result['label_center'][::-1]
        return result

    def restore(ir):
        return [transpose(ir[0], original['kind'])]

    def render(ir):
        raster = render_fn(restore(ir))
        return None if raster is None else np.swapaxes(raster, 0, 1)

    fitted = fit_labeled_square([transpose(original, 'UprightSquareKelleGlyph')],
        image=np.swapaxes(image, 0, 1), render_fn=render,
        error_fn=lambda raster: error_fn(np.swapaxes(raster, 0, 1)), _refine_contour=True,
        _squared_contour=_squared_contour)
    if fitted is not None:
        fitted['geometry_ir'] = restore(fitted['geometry_ir'])
        fitted['rendered'] = np.swapaxes(fitted['rendered'], 0, 1)
    return fitted


def _fit_left_stem_labeled_square(geometry_ir, *, image, render_fn, error_fn):
    """Reflect geometric coordinates while leaving the rendered label upright.

    Render in original axes before reflecting the raster: reflecting a finished
    SVG instead would mirror asymmetric letters such as P and p.
    """
    original = geometry_ir[0]
    render_evaluations = 0

    def render_original(ir):
        nonlocal render_evaluations
        render_evaluations += 1
        return render_fn(ir)

    def reflect(element, kind):
        result = copy.deepcopy(element)
        x, y, w, h = result['body_bbox']
        result.update(kind=kind, body_bbox=[1-x-w, y, w, h],
                      connector=[[1-u, v] for u, v in result['connector']])
        if 'label_center' in result:
            u, v = result['label_center']
            result['label_center'] = [1-u, v]
        return result

    def restore(ir):
        return [reflect(ir[0], original['kind'])]

    def render(ir):
        raster = render_original(restore(ir))
        return None if raster is None else raster[:, ::-1]

    initial = render_original(geometry_ir)
    if initial is None:
        return None
    initial_error = float(error_fn(initial))
    if not math.isfinite(initial_error):
        return None
    # A pale antialiased rim can minimize absolute error while missing its
    # darker core. Register the observed contour with squared color residuals.
    fitted = fit_labeled_square([reflect(original, 'RightStemSquareKelleGlyph')],
        image=image[:, ::-1], render_fn=render,
        error_fn=lambda raster: float(np.mean(np.sum(
            (image.astype(float)-raster[:, ::-1].astype(float))**2, axis=2))),
        _squared_contour=True)
    if fitted is not None:
        fitted['geometry_ir'] = restore(fitted['geometry_ir'])
        fitted['rendered'] = fitted['rendered'][:, ::-1]
        # Whole-image similarity can hide a wrong small letter. Compare the
        # observed interior contrast with the actual upright rendered glyph.
        blank_ir = copy.deepcopy(fitted['geometry_ir'])
        blank_ir[0]['label'] = ''
        blank = render_original(blank_ir)
        if blank is None:
            return None
        h, w = image.shape[:2]
        x, y, bw, bh = fitted['geometry_ir'][0]['body_bbox']
        margin = max(2., fitted['geometry_ir'][0]['body_stroke_width']*min(w, h)*1.5)
        interior = np.zeros((h, w), dtype=bool)
        interior[max(0, math.ceil(y*h+margin)):min(h, math.floor((y+bh)*h-margin)),
                 max(0, math.ceil(x*w+margin)):min(w, math.floor((x+bw)*w-margin))] = True
        observed = (np.max(np.abs(image.astype(float)-blank.astype(float)), axis=2) > 45) & interior
        predicted = (np.max(np.abs(fitted['rendered'].astype(float)-blank.astype(float)), axis=2) > 45) & interior
        gy, gx = np.where(predicted)
        union = np.count_nonzero(observed | predicted)
        label_iou = np.count_nonzero(observed & predicted)/max(1, union)
        if not len(gx) or label_iou < max(.6, 1-4/min(np.ptp(gx)+1, np.ptp(gy)+1)):
            return None
        final_error = float(error_fn(fitted['rendered']))
        if not math.isfinite(final_error) or final_error >= initial_error-1e-9:
            return None
        fitted.update(initial_error=initial_error, final_error=final_error,
                      render_evaluations=render_evaluations, label_iou=label_iou)
    return fitted


def fit_labeled_square(geometry_ir, *, image, render_fn, error_fn, _refine_contour=False, _squared_contour=False):
    """Fit observed geometry/colors while preserving the described text and topology.

    This handles one filled square with a connected lower, left or right stem and a
    single horizontal contrast label. It does not identify text from image IDs,
    access reference vectors, or turn arbitrary raster contours into paths.
    """
    if (len(geometry_ir) != 1 or geometry_ir[0].get('kind') not in {
            'UprightSquareKelleGlyph', 'RightStemSquareKelleGlyph', 'LeftRotatedSquareKelleTGlyph'}
            or len(str(geometry_ir[0].get('label', ''))) != 1):
        return None
    arr = np.asarray(image)
    if arr.ndim != 3 or arr.shape[2] != 3 or min(arr.shape[:2]) < 8 or not np.isfinite(arr).all():
        return None
    if geometry_ir[0]['kind'] == 'RightStemSquareKelleGlyph':
        return _fit_right_stem_labeled_square(geometry_ir, image=arr, render_fn=render_fn, error_fn=error_fn,
                                              _squared_contour=_squared_contour)
    if geometry_ir[0]['kind'] == 'LeftRotatedSquareKelleTGlyph':
        return _fit_left_stem_labeled_square(geometry_ir, image=arr, render_fn=render_fn, error_fn=error_fn)
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
    if _refine_contour:
        allowed = np.zeros_like(mask)
        allowed[max(0, top-1):bottom+1, max(0, left-1):right+1] = True
        allowed[bottom:stem_end, stem_left:stem_right] = True
        if np.any(mask & ~allowed):
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
    border_pixels = np.concatenate((arr[top, left:right], arr[bottom-1, left:right],
                                    arr[top:bottom, left], arr[top:bottom, right-1]))
    border_color = np.median(border_pixels, axis=0)
    border_core = np.percentile(border_pixels, 15, axis=0)
    # At fractional pixel phases, pale fill/white fringes can dominate the
    # outer row. Use the observed dark contour cores only when the median
    # has lost contrast; well-separated contour estimates stay unchanged.
    if (np.linalg.norm(border_color-body_color) < 50
            and np.linalg.norm(border_core-body_color) > 65):
        border_color = border_core
    stem_color = np.median(arr[bottom:stem_end, int(stem_center)], axis=0)
    original = render_fn(geometry_ir)
    if original is None:
        return None
    initial_error = float(error_fn(original))
    if not math.isfinite(initial_error):
        return None
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
            # Some historical directional kinds default to T when absent.
            # An explicit empty label is required for a truly blank body.
            blank['label'] = ''
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
    old_metrics = _contour_metrics(arr, best[2])
    if old_metrics[1] < .72 or _refine_contour:
        # An outer fringe can hide a thicker contour in a color/absolute-error
        # fit. Observe interior edge-band colors and jointly move the rectangle
        # and its stroke, preserving the observed outer pixel-center bounds.
        band = min(4, max(2, int(min(bw, bh)*.12)))
        pixels = np.concatenate((arr[top:top+band, left:right].reshape(-1, 3),
                                 arr[bottom-band:bottom, left:right].reshape(-1, 3),
                                 arr[top:bottom, left:left+band].reshape(-1, 3),
                                 arr[top:bottom, right-band:right].reshape(-1, 3)))
        contrast_pixels = pixels[(np.linalg.norm(pixels.astype(float)-body_color, axis=1) > 35)
                                 & (np.linalg.norm(pixels.astype(float)-255, axis=1) > 35)]
        if len(contrast_pixels):
            buckets = contrast_pixels // 8
            colors, counts = np.unique(buckets, axis=0, return_counts=True)
            core = np.median(contrast_pixels[np.all(buckets == colors[counts.argmax()], axis=1)], axis=0)
            candidate = copy.deepcopy(best[1])
            candidate['body_stroke'] = _hex(core)
            measured = measure(candidate)
            evaluations += 1
            probes = [measured] if measured is not None else []
            limit = min(6., min(bw, bh)*.2)
            for stroke in np.arange(.5, limit+.01, .5):
                candidate = copy.deepcopy(best[1])
                candidate.update(body_bbox=[(left+.5+stroke/2)/width, (top+.5+stroke/2)/height,
                                            (bw-1-stroke)/width, (bh-1-stroke)/height],
                                 body_stroke=_hex(core), body_stroke_width=stroke/scale)
                measured = measure(candidate)
                evaluations += 1
                if measured is not None:
                    probes.append(measured)
            def residual(measured):
                return float(np.mean(np.sum((arr.astype(float)-measured[2].astype(float))**2, axis=2)))
            if probes:
                refined = min(probes, key=residual)
                refined_score = residual(refined)
                # Pixel-center bounds are only a seed: antialiasing can move
                # the thresholded outer row by a fraction of a pixel.
                for step in (1., .5, .25, .125):
                    for _ in range(2):
                        changed = False
                        for field, index, divisor in (
                            ('body_bbox', 0, width), ('body_bbox', 1, height),
                            ('body_bbox', 2, width), ('body_bbox', 3, height),
                            ('body_stroke_width', None, scale),
                        ):
                            for sign in (-1, 1):
                                candidate = copy.deepcopy(refined[1])
                                if index is None:
                                    candidate[field] += sign*step/divisor
                                else:
                                    candidate[field][index] += sign*step/divisor
                                measured = measure(candidate)
                                evaluations += 1
                                if measured is not None and residual(measured) < refined_score-1e-9:
                                    refined, refined_score, changed = measured, residual(measured), True
                        if not changed:
                            break
                metrics = _contour_metrics(arr, refined[2])
                if (refined[0] < best[0]-1e-9 and metrics[0] <= old_metrics[0]+1e-9
                        and (_squared_contour or
                             (metrics[1] >= old_metrics[1]-1e-9 and metrics[2] >= old_metrics[2]-1e-9))):
                    best = refined
    if best[0] >= initial_error-1e-9:
        return None
    return {'geometry_ir': [best[1]], 'rendered': best[2], 'initial_error': initial_error,
            'final_error': best[0], 'evaluations': evaluations,
            'source': 'raster_labeled_square_registration_v1'}
