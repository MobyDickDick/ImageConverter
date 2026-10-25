"""Observe two vertical shafts, triangular heads and an optional crossbar.

Only native rectangles/triangles are emitted. Every primitive needs raster
support; row samples estimate geometry, never become output paths.
"""
from __future__ import annotations

import re
import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterDualArrowBadge import looksLikeDualArrowDescriptionImpl
from src.iCCModules.imageCompositeConverterFilledSymbols import _register, _hex
from src.iCCModules.imageCompositeConverterAdaptiveSearch import pixel_quality


def _runs(indices):
    return [part for part in np.split(indices, np.flatnonzero(np.diff(indices) > 1)+1) if len(part)]


def fit_arrow_pair(width, height, *, description, image, render_fn, error_fn):
    text = ' '.join(str(description or '').casefold().split())
    if not looksLikeDualArrowDescriptionImpl(text):
        return None
    arr = np.asarray(image)
    if arr.shape != (height, width, 3) or min(width, height) < 10:
        return None
    pixels = arr.astype(float)
    b, g, r = pixels.transpose(2, 0, 1)
    masks = [(b > r+30) & (b > g+15), (r > b+30) & (r > g+30)]
    geometries, colors, bars, centers = [], [], [], []
    for mask in masks:
        ys, xs = np.where(mask)
        if len(xs) < 12 or np.ptp(ys) < 12:
            return None
        # A shaft needs a long, independently observed vertical run.
        counts = mask.sum(axis=0)
        columns = np.flatnonzero(counts > counts.max()*.7)
        if len(_runs(columns)) != 1 or counts.max() < np.ptp(ys)*.45:
            return None
        color = np.percentile(pixels[mask], 5, axis=0)
        colors.extend(color)
        # White-background coverage resolves subpixel line width and center.
        channel = int(np.argmin(color))
        color_support = cv2.dilate(mask.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
        alpha = np.clip((255-pixels[:, :, channel]) / max(1, 255-color[channel]), 0, 1)*color_support
        row_width = mask.sum(axis=1)
        thin = np.flatnonzero((row_width > 0) & (row_width <= max(3, len(columns)+1)))
        if len(thin) < np.ptp(ys)*.4:
            return None
        shaft_rows = thin[(thin > np.percentile(ys, 10)) & (thin < np.percentile(ys, 65))]
        if len(shaft_rows) < 3:
            return None
        profile = np.median(alpha[shaft_rows], axis=0)
        sw = float(profile.sum())
        cx = float(np.dot(profile, np.arange(width)+.5)/max(sw, 1e-9))
        centers.append(cx)
        broad = _runs(np.flatnonzero(row_width > max(3, len(columns)+1)))
        # A viewport crop can leave only three widening rows of a head.
        heads = [run for run in broad if len(run) >= 3 and np.ptp(row_width[run]) >= 2
                 and abs(np.median([np.flatnonzero(mask[y]).mean()+.5 for y in run])-cx) <= max(2, sw*2)]
        if len(heads) != 1:
            return None
        head = heads[0]
        left = np.array([np.flatnonzero(mask[y])[0] for y in head], float)
        right = np.array([np.flatnonzero(mask[y])[-1]+1 for y in head], float)
        lf, rf = np.polyfit(head+.5, left, 1), np.polyfit(head+.5, right, 1)
        if lf[0]*rf[0] >= 0 or abs(lf[0]-rf[0]) < .3:
            return None
        if max(np.mean(abs(np.polyval(lf, head+.5)-left)),
               np.mean(abs(np.polyval(rf, head+.5)-right))) > .8:
            return None
        tip = float((rf[1]-lf[1])/(lf[0]-rf[0]))
        down = lf[0] > 0
        base = float(head[0] if down else head[-1]+1)
        tcx = float(np.polyval(lf, tip))
        half = float((np.polyval(rf, base)-np.polyval(lf, base))/2)
        if half <= sw or abs(tcx-cx) > max(1.5, sw):
            return None
        # Bottom heads may overlap the shaft; hidden endpoints are not fitted.
        if head.mean() < np.mean(ys) or abs(tip-base) > np.ptp(ys)*.4:
            return None
        geometries.extend([cx, float(ys.min()), float((tip+base)/2), sw, tcx, tip, base, half])
        for run in broad:
            if run is head:
                continue
            if len(run) > max(3, sw*4) or row_width[run].max() < width*.4:
                return None
            bar_profile = alpha[run].sum(axis=0)
            occupied = np.flatnonzero(bar_profile > .1)
            by_profile = alpha[:, occupied].sum(axis=1)
            by_profile[:run[0]] = 0
            by_profile[run[-1]+1:] = 0
            bar_height = float(np.median(alpha[run][:, occupied].sum(axis=0)))
            by = float(np.dot(by_profile, np.arange(height)+.5)/max(by_profile.sum(), 1e-9)-bar_height/2)
            bars.append((len(geometries)//8-1, [float(occupied[0]), by, float(occupied[-1]+1), bar_height]))
    if len(bars) > 1 or (geometries[5] > geometries[6]) == (geometries[13] > geometries[14]):
        return None
    order = np.argsort(centers)
    for side, index in zip(('links', 'rechts'), order):
        color = ('blau', 'rot')[index]
        if re.search(side+r'\s+(?:ist\s+)?'+('rot' if color == 'blau' else 'blau'), text):
            return None
        directions = [match[1] for clause in re.split(r'[.,;]', text)
                      if side in clause
                      for match in [re.search(r'spitze nach (oben|unten)', clause)] if match]
        expected = 'unten' if geometries[index*8+5] > geometries[index*8+6] else 'oben'
        if directions != [expected]:
            return None
    wants_bar = 'horizontal' in text or 'waagerecht' in text
    if wants_bar != bool(bars):
        return None
    bar_color = re.search(r'(rot\w*|blau\w*)\s+(?:horizontal\w*|waagerecht\w*)', text)
    if bars and bar_color and bars[0][0] != int(bar_color[1].startswith('rot')):
        return None
    foreground = np.min(pixels, axis=2) < 220
    supported = cv2.dilate((masks[0] | masks[1]).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    unexplained = foreground & ~supported
    if unexplained.sum() > max(2, foreground.sum()*.01):
        return None
    parameters = geometries + ([*bars[0][1]] if bars else []) + colors
    geometry_count = 16+4*len(bars)

    def build(p):
        parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
        for index in range(2):
            cx, top, bottom, sw, tcx, tip, base, half = p[index*8:index*8+8]
            color = _hex(np.array(p[geometry_count+index*3:geometry_count+index*3+3]))
            parts.append(f'<rect x="{cx-sw/2:.6f}" y="{top:.6f}" width="{sw:.6f}" height="{bottom-top:.6f}" fill="{color}"/>')
            parts.append(f'<polygon points="{tcx:.6f},{tip:.6f} {tcx-half:.6f},{base:.6f} {tcx+half:.6f},{base:.6f}" fill="{color}"/>')
        if bars:
            x1, y, x2, h = p[16:20]
            index = bars[0][0]
            color = _hex(np.array(p[geometry_count+index*3:geometry_count+index*3+3]))
            parts.append(f'<rect x="{x1:.6f}" y="{y:.6f}" width="{x2-x1:.6f}" height="{h:.6f}" fill="{color}"/>')
        return ''.join(parts)+'</svg>'

    def valid(p):
        for index in range(2):
            cx, top, bottom, sw, tcx, tip, base, half = p[index*8:index*8+8]
            if not (-2 <= top < bottom <= height+2 and .3 <= sw <= width*.15
                    and half > sw and abs(tip-base) >= 3 and abs(tcx-cx) <= 2
                    and abs(tip-base) < height*.4):
                return False
        return not bars or (p[18] > p[16] and .3 <= p[19] <= 4)

    background = np.median(np.concatenate((pixels[0], pixels[-1], pixels[:,0], pixels[:,-1])),axis=0)
    observed = np.max(abs(pixels-background), axis=2) > 25

    def loss(reference, rendered):
        predicted = np.max(abs(rendered.astype(float)-background), axis=2) > 25
        return float(np.mean((reference.astype(float)-rendered.astype(float))**2)
                     + 1000*np.mean(observed ^ predicted))

    result = _register(parameters, geometry_count, build, valid, arr, render_fn, error_fn,
                       'raster_arrow_pair_v1', loss_fn=loss,
                       refinement_steps=(1., .5, .25, .125, .0625, .03125))
    if result is None:
        return None
    quality = pixel_quality(arr, result['rendered'])
    if not quality or not quality['passed']:
        return None
    result['quality'] = quality
    return result
