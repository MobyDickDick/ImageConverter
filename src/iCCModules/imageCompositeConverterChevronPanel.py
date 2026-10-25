"""Register a framed vertical gradient and an open chevron from pixels."""
from __future__ import annotations

from itertools import product
import re

import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterAdaptiveSearch import current_search, pixel_quality


def downward_panel_contract(description):
    text = str(description or '').casefold().strip()
    extent = r'(?:geringfügig|etwas|ein wenig|leicht)'
    text = re.sub(r'\s+(?:das (?:gesamte )?motiv|die (?:gesamte )?darstellung) ist '+extent+
                  r' (?:grösser|kleiner) dargestellt und '+extent+
                  r' nach (?:links|rechts) und (?:oben|unten) (?:versetzt|verschoben)\.$', '', text)
    match = re.fullmatch(
        r'rechteckiges feld mit dünnem grauem rahmen und vertikalem (grünem|blauem|rotem|grauem) farbverlauf\. '
        r'eine weisse offene v-linie besteht aus zwei geraden schenkeln, '
        r'die sich unten in einer spitze treffen\.', text)
    return match[1] if match else None


def fit_chevron_panel(width, height, *, description, image, render_fn, error_fn):
    evaluations, render_cache = 0, {}
    session = current_search()
    downward = downward_panel_contract(description) is not None

    def cached_render(content, width, height):
        nonlocal evaluations
        if content not in render_cache:
            if downward and evaluations >= 1800:
                return None
            evaluations += 1
            if session:
                session.evaluations += 1
            if not downward and len(render_cache) >= 256:
                render_cache.clear()
            render_cache[content] = render_fn(content, width, height)
        return render_cache[content]

    def finish(candidate):
        if candidate is not None:
            candidate['evaluations'] = evaluations
            if downward:
                candidate['direction'] = 'down'
                candidate['hypotheses'] = attempts
        return candidate

    arguments = dict(description=description, image=image, render_fn=cached_render, error_fn=error_fn)
    incumbent = _fit_chevron_panel(width, height, **arguments)
    attempts = [{'loss': 'absolute', 'geometry': 'size', 'profile': 'uniform', 'evaluations': evaluations,
                 'error': incumbent['error'] if incumbent else None,
                 'quality': pixel_quality(image,incumbent['rendered']) if incumbent else None}]
    if incumbent is not None and pixel_quality(image, incumbent['rendered'])['passed']:
        return finish(incumbent)
    # Alternate photometric losses address different local minima. Keep the
    # original result unless an alternative passes the unchanged local gates.
    if not downward:
        attempts = []
    for refine_frame, squared_loss, preserve_peak in (
            (True, False, False), (True, True, False), (False, False, True)):
        if session and session.time_reason():
            break
        rendered_before = evaluations
        candidate = _fit_chevron_panel(width, height, refine_frame=refine_frame,
                                      squared_loss=squared_loss, preserve_peak=preserve_peak, **arguments)
        attempts.append({'loss': 'observed_peak' if preserve_peak and not downward else ('squared' if squared_loss else 'absolute'),
                         'geometry': 'sides' if refine_frame else 'size',
                         'profile': 'adaptive' if downward and preserve_peak else 'uniform',
                         'evaluations': evaluations-rendered_before,
                         'error': candidate['error'] if candidate else None,
                         'quality': pixel_quality(image,candidate['rendered']) if candidate else None})
        if candidate is not None and pixel_quality(image, candidate['rendered'])['passed']:
            candidate['frame_search'] = attempts
            return finish(candidate)
    return None if downward else finish(incumbent)


def _fit_chevron_panel(width, height, *, description, image, render_fn, error_fn,
                       refine_frame=False, squared_loss=False, preserve_peak=False):
    text = str(description or '').casefold()
    downward = downward_panel_contract(description)
    if downward is None:
        if not all(token in text for token in ('rechteck', 'rahm', 'vertikal', 'verlauf', 'dachlinie', 'oben')):
            return None
        if any(token in text for token in ('kreis', 'griff', 'text', 'beschrift', 'zusätzlich',
                                          'weitere', 'horizontaler verlauf', 'spitze unten')):
            return None
    arr = np.asarray(image)
    if arr.shape != (height, width, 3) or min(width, height) < 10:
        return None
    # Work in the same upward coordinate system for either direction. Emit
    # reflected native coordinates; saved SVGs need no transform or templates.
    if downward:
        arr = np.flip(arr, axis=0)
    mask = np.min(arr, axis=2) < 240
    ys, xs = np.nonzero(mask)
    if len(xs) < 30:
        return None
    x, y, w, h = cv2.boundingRect(np.column_stack((xs, ys)).astype(np.int32))
    if min(w, h) < 8 or mask[y:y+h, x:x+w].mean() < (.5 if refine_frame else .75):
        return None
    pixels = arr.astype(float)
    profile = np.median(pixels[y+2:y+h-2, x+2:x+w-2], axis=1)
    if np.ptp(profile, axis=0).max() < 8:
        return None
    if downward:
        b, g, r = np.median(profile, axis=0)
        palette = {'grünem': g > r+15 and g > b+10,
                   'blauem': b > r+20 and b > g+10,
                   'rotem': r > g+30 and r > b+30,
                   'grauem': max(b, g, r)-min(b, g, r) < 12}
        if not palette[downward]:
            return None
        # The only interior mark in this contract is white. A compact dark
        # deviation is an unexplained object even when global MSE is small.
        dark = (pixels[y+2:y+h-2, x+2:x+w-2]-profile[:,None,:]).mean(axis=2) < -35
        count, _, stats, _ = cv2.connectedComponentsWithStats(dark.astype(np.uint8))
        if count > 1 and stats[1:, cv2.CC_STAT_AREA].max() >= 4:
            return None
    # Compare each row against its dominant fill, which also works for an
    # achromatic panel with a dark mark rather than a white mark on color.
    deviation = np.linalg.norm(pixels[y+2:y+h-2, x+2:x+w-2]-profile[:, None, :], axis=2)
    mark = deviation > max(35., float(np.percentile(deviation, 95))*.45)
    my, mx = np.nonzero(mark)
    if len(mx) < max(8, w*.3):
        return None
    mx, my = mx.astype(float)+x+2.5, my.astype(float)+y+2.5
    # Each arm is estimated separately. Border pixels, compression fringes,
    # and the join cannot determine the slopes by themselves.
    lines = cv2.HoughLinesP(mark.astype(np.uint8), 1, np.pi/180,
                            max(4, int(w*.12)), minLineLength=max(4, w*.18), maxLineGap=3)
    if lines is None:
        return None
    arms = []
    for sign in (-1, 1):
        candidates = []
        for line in lines[:, 0]:
            ax, ay, bx, by = line.astype(float)+[x+2.5, y+2.5, x+2.5, y+2.5]
            if abs(bx-ax) < w*.15:
                continue
            slope = (by-ay)/(bx-ax)
            if .1 < sign*slope < 2:
                intercept = ay-slope*ax
                support = abs(my-slope*mx-intercept)/np.hypot(1, slope) < max(1.5, h*.06)
                candidates.append((int(support.sum()), slope, intercept, support))
        if not candidates:
            return None
        _, slope, intercept, support = max(candidates, key=lambda item: item[0])
        if support.sum() < max(4, w*.15) or np.ptp(mx[support]) < w*.25:
            return None
        slope, intercept = np.polyfit(mx[support], my[support], 1)
        arms.append((slope, intercept, support))
    left, right = arms
    px = float((right[1]-left[1])/(left[0]-right[0]))
    py = float(left[0]*px+left[1])
    if not (x+w*.2 < px < x+w*.8 and y-1 < py < y+h*.35):
        return None
    supported = left[2] | right[2]
    if supported.mean() < .85:
        return None
    if downward:
        unexplained = np.zeros(mark.shape,dtype=np.uint8)
        rows,cols = np.nonzero(mark)
        interior = ((mx > x+max(3,w*.05)) & (mx < x+w-max(3,w*.05))
                    & (my > y+max(3,h*.05)) & (my < y+h-max(3,h*.05)))
        unexplained[rows[~supported & interior],cols[~supported & interior]] = 1
        count,_,stats,_ = cv2.connectedComponentsWithStats(unexplained)
        if count > 1 and stats[1:,cv2.CC_STAT_AREA].max() >= 4:
            return None
    values = pixels[(my-.5).astype(int), (mx-.5).astype(int)]
    strengths = deviation[mark]
    shade = np.median(values[supported & (strengths > np.percentile(strengths[supported], 65))], axis=0)
    rim_samples = np.concatenate((pixels[y+2:y+h-2, x], pixels[y+2:y+h-2, x+w-1]))
    rim = np.median(rim_samples, axis=0)
    if refine_frame:
        # The outermost column can be antialiased background after a shift.
        # Estimate the thin dark frame from a narrow band inside each side.
        band = max(2, int(round(w*.06)))
        rim_samples = np.concatenate((pixels[y+2:y+h-2, x:x+band].reshape(-1, 3),
                                      pixels[y+2:y+h-2, x+w-band:x+w].reshape(-1, 3)))
        rim = np.percentile(rim_samples, 15, axis=0)
    hidden_frame = False
    if downward:
        # A translated crop can remove both side rims. Neutral observations
        # along the top/bottom still identify the gray frame independently.
        band = max(2, int(round(min(w, h)*.06)))
        samples = np.concatenate((pixels[y:y+band, x:x+w].reshape(-1,3),
                                  pixels[y+h-band:y+h, x:x+w].reshape(-1,3),
                                  pixels[y:y+h, x:x+band].reshape(-1,3),
                                  pixels[y:y+h, x+w-band:x+w].reshape(-1,3)))
        neutral = samples[(np.ptp(samples,axis=1) < 16) & (samples.max(axis=1) < 215)]
        if len(neutral) < max(3, min(w,h)*.15):
            # Accept an unobserved frame only when every side is cropped.
            # Its initial position is outside the viewport; no source geometry
            # or catalog-specific color is used to invent a visible edge.
            if (x,y,w,h) != (0,0,width,height):
                return None
            hidden_frame = True
            rim = np.repeat(np.median(samples.mean(axis=1)),3)
        else:
            rim = np.median(neutral,axis=0)
    if downward and (shade.min() < 210 or np.ptp(shade) > 20 or np.ptp(rim) > 30):
        return None
    # A bounded number of native gradient stops describes a continuous profile;
    # no per-pixel paths or reference vectors enter the runtime.
    indices = np.unique(np.rint(np.linspace(0, len(profile)-1, min(9, len(profile)))).astype(int))
    if downward and preserve_peak:
        # Compressed small rasters can contain an observable change in slope
        # between uniformly sampled rows. Compare a bounded adaptive profile.
        knots = [0, len(profile)-1]
        while len(knots) < min(9,len(profile)):
            approximation = np.column_stack([np.interp(np.arange(len(profile)),knots,profile[knots,c])
                                              for c in range(3)])
            deviation = np.linalg.norm(profile-approximation,axis=1)
            deviation[knots] = -1
            knots.append(int(np.argmax(deviation)))
            knots.sort()
        indices = np.asarray(knots)
    # Uniform subsampling can move a narrow near-white highlight by a row.
    # Preserve its observed peak within the same bounded stop count, rather
    # than letting a global fill shift create foreground in the adjacent row.
    peak = int(np.argmax(profile.mean(axis=1)))
    if preserve_peak and not downward and peak not in indices and len(indices) > 2:
        indices[1+int(np.argmin(abs(indices[1:-1]-peak)))] = peak
        indices.sort()
    stops = [(float((i+2.5)/h), profile[i]) for i in indices]
    endpoints = (float(x), float(left[0]*x+left[1]),
                 float(x+w), float(right[0]*(x+w)+right[1]))
    length = np.hypot(px-endpoints[0], py-endpoints[1])+np.hypot(endpoints[2]-px, endpoints[3]-py)
    stroke = float(np.clip(supported.sum()/length, .6, h*.2))
    # Rectangle, left endpoint, join, right endpoint, mark width and colors.
    p = [x+.5, y+.5, w-1., h-1., 1., *endpoints[:2], px, py, *endpoints[2:], stroke,
         *rim, *shade, 0., 0., 0.]
    if refine_frame:
        p[2:4] = [x+w-.5, y+h-.5]
    if hidden_frame:
        p[:4] = [-1.5,-1.5,width+3.,height+3.]
        if refine_frame:
            p[2:4] = [width+1.5,height+1.5]

    def color(value):
        return '#' + ''.join(f'{int(round(v)):02x}' for v in np.clip(value[::-1], 0, 255))

    def svg(values):
        rx, ry, rw, rh, bw, ax, ay, cx, cy, bx, by, sw = values[:12]
        if refine_frame:
            rw, rh = rw-rx, rh-ry
        gradient = ''.join(f'<stop offset="{offset:.6f}" stop-color="{color(shade+values[18:21])}"/>'
                           for offset, shade in stops)
        coordinates = (f'gradientUnits="userSpaceOnUse" x1="0" y1="{y}" x2="0" y2="{y+h}"'
                       if refine_frame else 'x1="0" y1="0" x2="0" y2="1"')
        if downward:
            coordinates = f'gradientUnits="userSpaceOnUse" x1="0" y1="{height-y}" x2="0" y2="{height-y-h}"'
            ry, ay, cy, by = height-ry-rh, height-ay, height-cy, height-by
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                f'<defs><linearGradient id="panel_fill" {coordinates}>{gradient}</linearGradient></defs>'
                f'<rect x="{rx:.6f}" y="{ry:.6f}" width="{rw:.6f}" height="{rh:.6f}" fill="url(#panel_fill)" '
                f'stroke="{color(values[12:15])}" stroke-width="{bw:.6f}"/>'
                f'<polyline points="{ax:.6f},{ay:.6f} {cx:.6f},{cy:.6f} {bx:.6f},{by:.6f}" fill="none" '
                f'stroke="{color(values[15:18])}" stroke-width="{sw:.6f}" stroke-linejoin="miter"/></svg>\n')

    evaluations, cache = 0, {}
    session = current_search()

    def measure(values):
        nonlocal evaluations
        if session and session.time_reason():
            return None
        content = svg(values)
        if content in cache:
            return cache[content]
        evaluations += 1
        rendered = render_fn(content, width, height)
        if rendered is None:
            return None
        error = float(error_fn(image, rendered))
        if downward:
            rendered = np.flip(rendered, axis=0)
        loss = float(np.mean((pixels-rendered.astype(float))**2)) if squared_loss else error
        result = (loss, content, rendered, error) if np.isfinite(error) and np.isfinite(loss) else None
        if len(cache) >= 256:
            cache.clear()
        cache[content] = result
        return result

    def valid(values):
        rx, ry, rw, rh, bw, ax, ay, cx, cy, bx, by, sw = values[:12]
        if refine_frame:
            rw, rh = rw-rx, rh-ry
        if downward and (abs(ax-rx) > max(1., sw) or abs(bx-rx-rw) > max(1., sw)
                         or min(values[15:18]) < 210 or np.ptp(values[15:18]) > 20
                         or np.ptp(values[12:15]) > 30):
            return False
        return (min(rw, rh) > 4 and .1 <= min(bw, sw) and max(bw, sw) < rh*.3
                and rx-2 <= ax < cx < bx <= rx+rw+2 and cy < min(ay, by)
                and ry-2 < cy < ry+rh*.4 and max(ay, by) < ry+rh)

    best = measure(p)
    if best is None:
        return None
    initial_error = best[3]
    if refine_frame:
        # Move the four sides jointly before fitting color. Otherwise a bright
        # rim can hide misplaced sides and trap subsequent single-value steps.
        seed = p.copy()
        for shifts in product((-1.5, 0., 1.5), repeat=4):
            candidate = seed.copy()
            candidate[:4] = [value+shift for value, shift in zip(seed[:4], shifts)]
            if valid(candidate):
                measured = measure(candidate)
                if measured is not None and measured[0] < best[0]-1e-9:
                    p, best = candidate, measured
    for step in (1., .5, .25, .125):
        for _ in range(2):
            for index in range(len(p)):
                for sign in (-1., 1.):
                    candidate = p.copy()
                    candidate[index] += sign*step*(8 if index >= 12 else 1)
                    if not valid(candidate):
                        continue
                    measured = measure(candidate)
                    if measured is not None and measured[0] < best[0]-1e-9:
                        p, best = candidate, measured
    if best[3] > initial_error or not valid(p):
        return None
    residual = np.max(np.abs(pixels-best[2].astype(float)), axis=2) > 65
    if residual.mean() > .04:
        return None
    reported_parameters = p.copy()
    if refine_frame:
        reported_parameters[2:4] = [p[2]-p[0], p[3]-p[1]]
    if downward:
        reported_parameters[1] = height-reported_parameters[1]-reported_parameters[3]
        for index in (6, 8, 10):
            reported_parameters[index] = height-reported_parameters[index]
    return {'svg': best[1], 'rendered': np.flip(best[2], axis=0) if downward else best[2],
            'error': best[3], 'initial_error': initial_error,
            'parameters': reported_parameters, 'evaluations': evaluations, 'source': 'raster_chevron_panel_v1'}
