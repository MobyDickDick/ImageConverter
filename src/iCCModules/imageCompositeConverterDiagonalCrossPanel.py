"""Fit a framed panel, an interior plus and a clipped outlined diagonal.

All geometry and paint are estimated from raster evidence. The description
selects the inventory; no reference vectors or image identifiers are used.
"""
from __future__ import annotations

import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterAdaptiveSearch import pixel_quality
from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _register


def fit_diagonal_cross_panel(width, height, *, description, image, render_fn, error_fn):
    text = ' '.join(str(description or '').casefold().split())
    if not (all(t in text for t in ('rechteck', 'rand', 'kreuz', 'oben links', 'diagonal',
                                    'unten links', 'oben rechts', 'mittellinie'))
            and 'seitenlinie' in text
            and any(t in text for t in ('abgeschnitten', 'abgeschnitt', 'begrenzt'))):
        return None
    if any(t in text for t in ('kreis', 'text', 'beschrift', 'zwei kreuze', 'ohne kreuz',
                               'kein kreuz', 'ohne mittellinie', 'keine seitenlinien')):
        return None
    arr = np.asarray(image)
    if arr.shape != (height, width, 3) or min(width, height) < 16 or height < width:
        return None
    pixels = arr.astype(float)
    yy, xx = np.indices((height, width), dtype=float)
    xx += .5
    yy += .5
    # The light sides must independently support a long ascending diagonal.
    middle = (yy > height*.22) & (yy < height*.82) & (xx > 2) & (xx < width-2)
    weights = np.maximum(0, np.min(pixels, axis=2)-100)*middle
    rows = np.flatnonzero(weights.sum(axis=1) > 20)
    if len(rows) < height*.35:
        return None
    centers = (weights[rows]*xx[rows]).sum(axis=1)/weights[rows].sum(axis=1)
    slope, intercept = np.polyfit(rows+.5, centers, 1)
    if not (-2 < slope < -.15) or np.mean(abs(centers-(slope*(rows+.5)+intercept))) > 1:
        return None
    distance = abs(xx-(slope*yy+intercept))/np.hypot(1, slope)
    # Background paint comes from exposed panel pixels, excluding both marks.
    exposed = (distance > 3) & (yy > 2) & (yy < height-2) & (xx > 2) & (xx < width-2)
    exposed &= ~((xx < width*.55) & (yy < height*.26))
    knots = np.array([.1, .4, .9])*width
    palette = []
    for x in knots:
        region = exposed & (abs(xx-x) < max(2, width*.13))
        if region.sum() < 8:
            return None
        palette.append(np.median(pixels[region], axis=0))
    field = np.stack([np.interp(xx, knots, [c[channel] for c in palette])
                      for channel in range(3)], axis=2)
    darkness = np.max(field, axis=2)-np.max(pixels, axis=2)
    upper_left = (xx > width*.12) & (xx < width*.55) & (yy > height*.03) & (yy < height*.28)
    mark = upper_left & (darkness > 40) & (distance > 3)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mark.astype('uint8'))
    if count < 2:
        return None
    i = 1+int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    x, y, w, h, area = stats[i]
    if min(w, h) < 3 or area < 8 or not .45 < w/h < 2:
        return None
    core = labels == i
    cx, cy = x+w/2, y+h/2
    # Independent arm support keeps a dark disk from standing in for a plus.
    if not (core[int(cy), x:x+w].sum() >= w*.6
            and core[y:y+h, int(cx)].sum() >= h*.6):
        return None
    light = (distance > .6) & (distance < 1.5) & middle
    dark = (distance < .45) & middle
    rim = np.concatenate((pixels[1, 2:-2], pixels[-2, 2:-2], pixels[2:-2, 1], pixels[2:-2, -2]))
    colors = [np.median(np.concatenate((pixels[:, 0], pixels[:, -1])), axis=0),
              np.median(rim, axis=0), *palette, np.percentile(pixels[light], 80, axis=0),
              np.median(pixels[dark], axis=0), np.median(pixels[core], axis=0)]
    # Frame bounds/stroke, diagonal at both viewport ends/widths, plus center,
    # independent arm lengths, arm thickness and a soft raster-supported halo.
    p = [1.3, 1.1, width-2.6, height-2.2, 1.2,
         intercept, slope*height+intercept, 2.5, .85,
         cx, cy, w/2, h/2, max(1, min(w, h)*.36), 1.,
         *np.asarray(colors).ravel()]
    geometry_count = 15

    def build(v):
        x, y, w, h, rim_width, top, bottom, outer, inner, cx, cy, rx, ry, arm, halo = v[:15]
        colors = [_hex(v[k:k+3]) for k in range(15, len(v), 3)]
        stops = ''.join(f'<stop offset="{t}" stop-color="{c}"/>'
                        for t, c in zip((0, .4, 1), colors[2:5]))
        points = [(cx-arm/2,cy-ry),(cx+arm/2,cy-ry),(cx+arm/2,cy-arm/2),
                  (cx+rx,cy-arm/2),(cx+rx,cy+arm/2),(cx+arm/2,cy+arm/2),
                  (cx+arm/2,cy+ry),(cx-arm/2,cy+ry),(cx-arm/2,cy+arm/2),
                  (cx-rx,cy+arm/2),(cx-rx,cy-arm/2),(cx-arm/2,cy-arm/2)]
        plus = ' '.join(f'{a:.6f},{b:.6f}' for a,b in points)
        halo_color = _hex((np.asarray(v[36:39])+np.asarray(v[21:24]))/2)
        diagonal = f'M {top:.6f},0 L {bottom:.6f},{height}'
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                f'<defs><linearGradient id="panelPaint">{stops}</linearGradient>'
                f'<clipPath id="panelClip"><rect x="{x:.6f}" y="{y:.6f}" '
                f'width="{w:.6f}" height="{h:.6f}"/></clipPath></defs>'
                f'<rect width="{width}" height="{height}" fill="{colors[0]}"/>'
                f'<rect x="{x:.6f}" y="{y:.6f}" width="{w:.6f}" height="{h:.6f}" fill="url(#panelPaint)"/>'
                f'<g clip-path="url(#panelClip)"><path d="{diagonal}" stroke="{colors[5]}" stroke-width="{outer:.6f}"/>'
                f'<path d="{diagonal}" stroke="{colors[6]}" stroke-width="{inner:.6f}"/>'
                f'<polygon points="{plus}" fill="{colors[7]}" stroke="{halo_color}" stroke-width="{halo:.6f}" stroke-linejoin="round"/>'
                f'<polygon points="{plus}" fill="{colors[7]}"/></g>'
                f'<rect x="{x:.6f}" y="{y:.6f}" width="{w:.6f}" height="{h:.6f}" fill="none" '
                f'stroke="{colors[1]}" stroke-width="{rim_width:.6f}"/></svg>')

    def valid(v):
        x,y,w,h,rim,top,bottom,outer,inner,cx,cy,rx,ry,arm,halo = v[:15]
        return (np.isfinite(v).all() and -.5 <= x <= width*.15 and -.5 <= y <= height*.1
                and width*.7 < w <= width+1 and height*.7 < h <= height+1
                and .3 <= rim <= min(w,h)*.15 and .3 < inner and inner+.3 < outer < width*.2
                and width*.6 < top < width+3 and -3 < bottom < width*.4
                and x+rx < cx < x+w*.55 and y+ry < cy < y+h*.3
                and 1 < rx < w*.2 and 1 < ry < h*.15 and .5 < arm <= min(rx,ry)
                and 0 <= halo < arm*.65 and np.min(v[30:33]-v[33:36]) > 35
                and np.all((v[15:] >= 0) & (v[15:] <= 255)))

    def loss(reference, rendered):
        delta = np.mean((reference.astype(float)-rendered.astype(float))**2, axis=2)
        local = delta[max(0,y-2):min(height,y+h+2), max(0,x-2):min(width,x+w+2)]
        return float(delta.mean()+local.mean())

    def details(rendered):
        error = np.mean((pixels-rendered.astype(float))**2, axis=2)/255**2
        cross_error = float(error[max(0,y-2):min(height,y+h+2), max(0,x-2):min(width,x+w+2)].mean())
        diagonal_error = float(error[(distance < 2.25) & middle].mean())
        return dict(cross_mse=cross_error, diagonal_mse=diagonal_error,
                    passed=bool(cross_error <= .02 and diagonal_error <= .02))

    result = _register(p, geometry_count, build, valid, arr, render_fn, error_fn,
                       'raster_diagonal_cross_panel_v1', loss_fn=loss,
                       satisfactory_fn=lambda p,m: details(m[3])['passed'],
                       refinement_steps=(1., .5, .25, .125, .0625))
    if result is None:
        return None
    result['quality'] = pixel_quality(arr, result['rendered'])
    result['details'] = details(result['rendered'])
    return result if result['quality']['passed'] and result['details']['passed'] else None
