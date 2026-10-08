"""Fit a horizontal gradient panel, repeated zigzag and open inner frame."""
from __future__ import annotations

import cv2
import numpy as np


def fit_zigzag_panel(width, height, *, description, image, render_fn, error_fn):
    text = str(description or '').casefold()
    repeated = 'liniengruppe' in text and 'balken' in text
    if not all(t in text for t in ('rechteck', 'rahm', 'horizontal', 'verlauf', 'link', 'recht', 'ungefüllt')):
        return None
    if not repeated and 'zickzack' not in text:
        return None
    if any(t in text for t in ('kreis', 'andreaskreuz', 'diagonal', 'griff', 'zusätzlich', 'vertikaler verlauf')):
        return None
    arr = np.asarray(image)
    if arr.shape != (height, width, 3) or min(width, height) < 16:
        return None
    pixels = arr.astype(float)
    ys, xs = np.nonzero(np.min(arr, axis=2) < 240)
    if len(xs) < 50:
        return None
    x, y, w, h = cv2.boundingRect(np.column_stack((xs, ys)).astype(np.int32))
    if h <= w or min(w, h) < 16:
        return None
    profile = np.median(pixels[y+2:y+h-2, x:x+w], axis=0)
    gray = profile.mean(axis=1)
    smooth = cv2.GaussianBlur(gray[:, None], (1, 0), max(2, w*.06)).ravel()
    candidates = [i for i in range(3, w-2) if gray[i] <= min(gray[i-1], gray[i+1])
               and gray[i] < max(gray[i-1], gray[i+1])
               and gray[i]-smooth[i] < -8 and i > w*.3]
    groups = []
    for i in candidates:
        if groups and i-groups[-1][-1] <= 2:
            groups[-1].append(i)
        else:
            groups.append([i])
    troughs = [int(round(np.mean(group))) for group in groups]
    if len(troughs) != 2:
        return None
    left, right = troughs
    if not w*.3 < left < right < w-1 or right-left < w*.2:
        return None
    # The vertical edges are removed before estimating the underlying fill.
    clean = profile.copy()
    for edge in troughs:
        lo, hi = max(0, edge-1), min(w-1, edge+1)
        clean[lo:hi+1] = np.linspace(profile[lo], profile[hi], hi-lo+1)
    # Repeated deviations from the column fill supply both period and phase;
    # neither is copied from a catalog or inferred from the image filename.
    rail_columns = np.flatnonzero(gray[:left//2] < gray.max()-60)
    if repeated and (len(rail_columns) < 2 or np.any(np.diff(rail_columns) != 1)):
        return None
    if repeated:
        first_fill = int(rail_columns[-1])+2
        slope = profile[first_fill+1]-profile[first_fill]
        for i in range(first_fill):
            clean[i] = profile[first_fill]+(i-first_fill)*slope
    indices = np.unique(np.rint(np.linspace(0 if repeated else 2, w-3, min(9, w-4))).astype(int))
    shades = clean[indices]
    start = x+int(rail_columns[-1])+2 if repeated else x+3
    end = x+left-2
    if end-start < 3:
        return None
    deviation = np.maximum(0, (profile[start-x:end-x][None, :, :]-pixels[y+2:y+h-2, start:end]).mean(axis=2))
    if not repeated:
        active = np.flatnonzero((deviation > 12).sum(axis=0) > h*.04)
        if len(active) < 3:
            return None
        deviation = deviation[:, active[0]:active[-1]+1]
        end = start+int(active[-1])+1
        start += int(active[0])
    signature = (deviation if repeated else deviation[:, :max(1, (end-start)//3)]).sum(axis=1)
    signature -= signature.mean()
    if np.std(signature) < 4:
        return None
    correlations = [(float(np.sum(signature[:-lag]*signature[lag:]) /
                           max(1e-9, np.linalg.norm(signature[:-lag])*np.linalg.norm(signature[lag:]))), lag)
                    for lag in range(4, max(5, h//3))]
    peaks = [(score, lag) for score, lag in correlations if score > (.35 if repeated else .5)
             and all(score >= other for other, l in correlations if abs(l-lag) == 1)]
    if repeated:
        turns = [i for i in range(1, len(signature)-1) if signature[i] > signature.max()*.4
                 and signature[i] >= max(signature[i-1], signature[i+1])]
        centers = []
        for i in turns:
            if centers and i-centers[-1][-1] <= 1:
                centers[-1].append(i)
            else:
                centers.append([i])
        centers = np.array([np.mean(group) for group in centers])
        if len(centers) < 3:
            return None
        spacing = float(np.median(np.diff(centers)))
        lattice = np.rint((centers-centers[0])/spacing)
        period, origin = np.polyfit(lattice, centers, 1)
        if not 4 < period < h/3 or np.max(np.abs(centers-(origin+lattice*period))) > period*.15:
            return None
        phase = float(y+2+origin)
    else:
        if not peaks:
            return None
        period = float(min(peaks, key=lambda item: item[1])[1])
    # A folded spatial signature locates the left-hand zigzag turns.
    weights = (deviation if repeated else deviation[:, :max(1, (end-start)//3)]).sum(axis=1)
    folded = np.array([weights[np.arange(len(weights)) % int(period) == i].mean() for i in range(int(period))])
    if not repeated:
        phase = float(y+2+np.argmax(folded))
    lx, rx = float(start-.5), float(end-.5)
    # Horizontal frame edges are visible in the right rectangle's row profile.
    row = pixels[y:y+h, x+left+2:x+right-1].mean(axis=(1, 2))
    top = y+int(np.argmin(row[1:max(3, h//5)]))+1
    bottom = y+h-max(3, h//5)+int(np.argmin(row[-max(3, h//5):-1]))
    rim = np.median(np.concatenate((pixels[y, x:x+w], pixels[y+h-1, x:x+w])), axis=0)
    inner = (profile[left]+profile[right])/2
    mark = np.median(pixels[y+2:y+h-2, start:end][deviation > np.percentile(deviation, 85)], axis=0)
    # Outer frame; inner frame; zigzag; three observed stroke colors; fill shift.
    p = [x+.5, y+.5, w-1., h-1., 1., x+left+.5, top+.5, right-left, bottom-top, 1.,
         lx, rx, period, phase, .7, *rim, *inner, *mark, 0., 0., 0.]
    if repeated:
        my, mx = np.nonzero(deviation > max(25, np.percentile(deviation, 85)))
        if len(mx) < 10:
            return None
        p[10:12] = [float(start+mx.min()+.5), float(start+mx.max()+.5)]
        rail_x = x+float(rail_columns[0])
        rail_width = float(rail_columns[-1]-rail_columns[0]+1)
        rail_mask = pixels[:, int(rail_x+rail_width/2)].mean(axis=1) < gray.max()-60
        observed_y = np.flatnonzero(rail_mask)
        p.extend([rail_x, float(observed_y.min()), rail_width, float(observed_y.max()-observed_y.min()+1),
                  period*.12, period*.4, 0., float(start)-rail_x-rail_width,
                  *np.median(pixels[observed_y, int(rail_x+rail_width/2)], axis=0)])

    def color(v):
        return '#' + ''.join(f'{int(round(c)):02x}' for c in np.clip(v[::-1], 0, 255))

    def points(v):
        ax, bx, cycle, origin = v[10:14]
        low, high = v[1], v[1]+v[3]
        first = int(np.floor((low-origin)/(cycle/2)))+1
        last = int(np.ceil((high-origin)/(cycle/2)))
        def at(t):
            f = ((t-origin)/cycle) % 1
            return ax+(bx-ax)*(1-abs(2*f-1))
        return [(at(low), low)] + [(ax if k % 2 == 0 else bx, origin+k*cycle/2)
                                   for k in range(first, last)] + [(at(high), high)]

    def valid(v):
        ox, oy, ow, oh, bw, ix, iy, iw, ih, sw = v[:10]
        ax, bx, cycle, _, zw = v[10:15]
        return (np.isfinite(v).all() and min(ow, oh, iw, ih) > 3 and oh > ow
                and ox < ax < bx < ix < ix+iw < ox+ow and oy < iy < iy+ih < oy+oh
                and 4 <= cycle <= oh/3 and .1 <= min(bw, sw, zw) and max(bw, sw, zw) < ow*.2
                and (not repeated or (ox-1 <= v[27] < v[27]+v[29] < ax and v[29] > .2
                     and oh*.6 < v[30] <= oh+2 and 0 <= v[31] < v[32] < cycle/2
                     and 0 <= v[33] < ix-bx and 0 <= v[34] < ax-v[27])))

    def svg(v):
        ox, oy, ow, oh, bw, ix, iy, iw, ih, sw = v[:10]
        stops = ''.join(f'<stop offset="{(i+.5)/w:.6f}" stop-color="{color(shade+v[24:27])}"/>'
                        for i, shade in zip(indices, shades))
        coords = ' '.join(f'{a:.6f},{b:.6f}' for a,b in points(v))
        if repeated:
            ax, bx, cycle, origin, zw = v[10:15]
            rail_x, rail_y, rail_w, rail_h, gap, rise, extension, connection = v[27:35]
            mark_svg = (f'<rect x="{rail_x:.6f}" y="{rail_y:.6f}" width="{rail_w:.6f}" height="{rail_h:.6f}" fill="{color(v[35:38])}"/>'
                        f'<g stroke="{color(v[21:24])}" stroke-width="{zw:.6f}">')
            for k in range(int(np.ceil((oy-origin)/cycle)), int(np.floor((oy+oh-origin)/cycle))+1):
                cy = origin+k*cycle
                for a,b,c,d in [(ax,cy-gap,bx,cy-rise), (ax,cy,bx+extension,cy),
                                (ax,cy+gap,bx,cy+rise), (ox,cy,rail_x+rail_w+connection,cy)]:
                    mark_svg += f'<path d="M {a:.6f} {b:.6f} L {c:.6f} {d:.6f}"/>'
            mark_svg += '</g>'
        else:
            mark_svg = f'<polyline points="{coords}" fill="none" stroke="{color(v[21:24])}" stroke-width="{v[14]:.6f}"/>'
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                f'<defs><linearGradient id="panel_fill" x1="0" y1="0" x2="1" y2="0">{stops}</linearGradient></defs>'
                f'<rect x="{ox:.6f}" y="{oy:.6f}" width="{ow:.6f}" height="{oh:.6f}" fill="url(#panel_fill)" stroke="{color(v[15:18])}" stroke-width="{bw:.6f}"/>'
                f'<rect x="{ix:.6f}" y="{iy:.6f}" width="{iw:.6f}" height="{ih:.6f}" fill="none" stroke="{color(v[18:21])}" stroke-width="{sw:.6f}"/>'
                f'{mark_svg}</svg>\n')

    evaluations = 0
    border = np.concatenate((pixels[0], pixels[-1], pixels[:, 0], pixels[:, -1]))
    background = np.median(border, axis=0)
    reference_contrast = np.max(np.abs(pixels-background), axis=2) > 25
    def measure(v):
        nonlocal evaluations
        if not valid(v):
            return None
        evaluations += 1
        content = svg(v)
        raster = render_fn(content, width, height)
        if raster is None:
            return None
        error = float(error_fn(image, raster))
        if not np.isfinite(error):
            return None
        score = float(np.square(pixels-raster.astype(float)).mean())
        if repeated:
            contrast = np.max(np.abs(raster.astype(float)-background), axis=2) > 25
            score += 1000*float((contrast != reference_contrast).mean())
        return score, content, raster, error

    best = measure(p)
    if best is None:
        return None
    initial_error = best[3]
    for step in (1., .5, .25, .125):
        for _ in range(2):
            for index in range(len(p)):
                for sign in (-1, 1):
                    candidate = p.copy()
                    candidate[index] += sign*step*(8 if 15 <= index < 27 or index >= 35 else 1)
                    result = measure(candidate)
                    if result is not None and result[0] < best[0]-1e-9:
                        p, best = candidate, result
    if repeated:
        # Refine the bounded gradient palette independently of the strokes.
        # A dark rail cannot be allowed to stand in for the hidden panel fill.
        for step in (8., 4., 2., 1.):
            for index in range(len(shades)):
                for sign in (-1, 1):
                    old = shades[index].copy()
                    shades[index] = old+sign*step
                    result = measure(p)
                    if result is not None and result[0] < best[0]-1e-9:
                        best = result
                    else:
                        shades[index] = old
    if best[3] >= initial_error-1e-9:
        return None
    if (np.max(np.abs(pixels-best[2].astype(float)), axis=2) > 65).mean() > .04:
        return None
    return {'svg': best[1], 'rendered': best[2], 'error': best[3], 'initial_error': initial_error,
            'parameters': p, 'evaluations': evaluations,
            'source': 'raster_repeated_line_panel_v1' if repeated else 'raster_zigzag_panel_v1'}
