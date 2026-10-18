"""Register a described single dark letter inside a filled outlined disk."""
from __future__ import annotations

import re
import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _image, _register


def fit_labeled_disk(width, height, *, description, image, render_fn, error_fn):
    text = str(description or '')
    words = text.casefold()
    letters = re.findall(r'(?i:einzelne[nr]? dunkle[nr]? (?:großbuchstabe|buchstabe))\s+["„]([A-Z])["“]', text)
    letter = letters[0] if len(letters) == 1 else None
    bottom_stem = bool(re.search(r'am unteren rand.*mittig.*senkrechter.*griff nach unten', words))
    forbidden = ('zusätzlich', 'verlauf', 'zwei buchstaben', 'ohne buchstabe', 'dreieck', 'leitung')
    if (letter is None or not all(t in words for t in
            ('kreisscheibe', 'einfarbig', 'dunkle', 'randkontur', 'einzelne', 'serifenlos'))
            or any(t in words for t in forbidden)
            or (not bottom_stem and ('griff' in words or not re.search(r'keine anschlüsse', words)))
            or (bottom_stem and any(t in words for t in ('keine anschlüsse', 'ohne griff', 'griff nach oben', 'griff nach links', 'griff nach rechts')))):
        return None
    label = letter
    pixels = _image(width, height, image)
    if pixels is None:
        return None
    border = np.concatenate((pixels[0], pixels[-1], pixels[:, 0], pixels[:, -1]))
    if np.min(np.median(border, axis=0)) < 245:
        return None
    mask = (np.min(pixels, axis=2) < 210).astype(np.uint8)
    contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]
    if not contours:
        return None
    outline = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(outline)
    silhouette = np.zeros_like(mask)
    cv2.drawContours(silhouette, [outline], -1, 1, -1)
    if (not bottom_stem and (not .85 < w/h < 1.18 or silhouette.sum() < .65*w*h)
            or np.count_nonzero(mask & ~silhouette) > max(2, silhouette.sum()*.005)):
        return None
    contour = outline[:, 0].astype(float)+.5
    if bottom_stem:
        # Fit the circular head from its top and flanks; the narrow lower
        # connector must not pull the circle center/radius toward its endpoint.
        contour = contour[(contour[:, 1] < y+w*.5) | (np.abs(contour[:, 0]-(x+w/2)) > w*.2)]
        if len(contour) < 12:
            return None
    coefficients = np.linalg.lstsq(np.c_[2*contour, np.ones(len(contour))], (contour**2).sum(axis=1), rcond=None)[0]
    cx, cy = coefficients[:2]
    radius = float(np.sqrt(max(0, coefficients[2]+cx*cx+cy*cy)))
    if radius < 5 or np.mean(np.abs(np.linalg.norm(contour-[cx, cy], axis=1)-radius)) > max(.6, radius*.035):
        return None
    stem_end = stem_width = stem_color = None
    if bottom_stem:
        start = int(np.ceil(cy+radius+1))
        sy, sx = np.where(mask[start:])
        if not len(sy):
            return None
        left, right = sx.min(), sx.max()+1
        if (right-left > radius*.45 or abs((left+right)/2-cx) > radius*.12
                or sy.min() > 0 or not np.array_equal(np.unique(sy), np.arange(sy.max()+1))
                or mask[start:start+sy.max()+1, left:right].mean() < .85):
            return None
        stem_end, stem_width = float(start+sy.max()+1), float(right-left)
        stem_color = np.percentile(pixels[start:][mask[start:].astype(bool)], 15, axis=0)
        yy0, xx0 = np.indices(mask.shape)
        allowed = (np.hypot(xx0+.5-cx, yy0+.5-cy) < radius+1.5)
        allowed |= (np.abs(xx0+.5-cx) <= stem_width/2+1) & (yy0 >= cy) & (yy0 < stem_end)
        if np.any(mask.astype(bool) & ~allowed):
            return None
    geometry_count = 9 if bottom_stem else 7
    yy, xx = np.indices((height, width), dtype=float)
    radial = np.hypot(xx+.5-cx, yy+.5-cy)
    body = pixels[(radial > radius*.55) & (radial < radius*.78)]
    if len(body) < 8:
        return None
    fill = np.median(body, axis=0)
    # Interior contrast evidence must form one letter, separate from the rim.
    glyph_mask = ((np.mean(fill-pixels, axis=2) > 45) & (radial < radius*.8)).astype(np.uint8)
    count, glyph_labels, glyph_stats, _ = cv2.connectedComponentsWithStats(glyph_mask)
    if count < 2:
        return None
    gi = 1+int(np.argmax(glyph_stats[1:, cv2.CC_STAT_AREA]))
    gx, gy, gw, gh, ga = glyph_stats[gi]
    if (min(gw, gh) < 2 or ga < 4 or ga > 1.3*radius*radius
            or sum(glyph_stats[i, cv2.CC_STAT_AREA] for i in range(1, count) if i != gi) > max(2, ga*.03)):
        return None
    color = np.percentile(pixels[glyph_labels == gi], 15, axis=0)
    dark = np.percentile(pixels[(radial > radius*.92) & (radial < radius*1.03)], 15, axis=0)
    if fill.mean() < dark.mean()+35:
        return None

    def build(p, *, blank=False):
        p = np.asarray(p)
        cx, cy, r, stroke, tx, ty, size = p[:7]
        fill, dark, color = p[geometry_count:geometry_count+9].reshape(-1, 3)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                f'<rect width="{width}" height="{height}" fill="#ffffff"/>'
                + (f'<line x1="{cx:.4f}" y1="{cy+r:.4f}" x2="{cx:.4f}" y2="{p[7]:.4f}" stroke="{_hex(p[-3:])}" stroke-width="{p[8]:.4f}"/>' if bottom_stem else '')
                + f'<circle cx="{cx:.4f}" cy="{cy:.4f}" r="{r:.4f}" fill="{_hex(fill)}" stroke="{_hex(dark)}" stroke-width="{stroke:.4f}"/>'
                + ('' if blank else f'<text x="{tx:.4f}" y="{ty:.4f}" font-family="Arial" font-weight="700" font-size="{size:.4f}" text-anchor="middle" fill="{_hex(color)}">{label}</text>')+'</svg>\n')

    p = np.r_[cx, cy, radius-.15, max(.5, radius*.09), gx+gw/2, gy+gh, gh*1.35, fill, dark, color]
    if bottom_stem:
        p = np.r_[p[:7], stem_end, stem_width, p[7:], stem_color]
    # The observed outer contour includes the stroke. Seed a circle whose
    # complete stroke fits the canvas, also for tightly cropped disks.
    inset_radius = min(cx, width-cx, cy, height-cy)-p[3]/2
    # Keep one SVG rounding unit inside the boundary to avoid floating-point
    # cancellation rejecting an otherwise valid initial candidate.
    p[2] = min(p[2], inset_radius-1e-4)
    # Use the production font's observed bounds to seed size and baseline.
    for _ in range(3):
        drawn, blank = render_fn(build(p), width, height), render_fn(build(p, blank=True), width, height)
        if drawn is None or blank is None:
            return None
        ty, tx = np.where(np.max(np.abs(drawn.astype(float)-blank.astype(float)), axis=2) > 45)
        if not len(tx):
            return None
        p[4] += gx+gw/2-(tx.min()+tx.max()+1)/2
        p[5] += gy+gh/2-(ty.min()+ty.max()+1)/2
        p[6] *= gh/(ty.max()-ty.min()+1)

    def valid(p):
        cx, cy, r, stroke, tx, ty, size = p[:7]
        return (r > 4 and .15 <= stroke <= r*.2
                and 0 <= cx-r-stroke/2 and cx+r+stroke/2 <= width and 0 <= cy-r-stroke/2 and cy+r+stroke/2 <= height
                and abs(tx-cx) < r*.25 and cy < ty < cy+r*.8 and 3 <= size < r*1.9
                and (not bottom_stem or (cy+r+.5 < p[7] <= height and .3 <= p[8] < r*.45))
                and np.isfinite(p).all() and np.all((p[geometry_count:] >= 0) & (p[geometry_count:] <= 255)))

    semantic_evaluations = 0
    def satisfactory(parameters, measured):
        nonlocal semantic_evaluations
        blank = render_fn(build(parameters,blank=True),width,height)
        semantic_evaluations += 1
        if blank is None:
            return False
        output = measured[3].astype(float)
        predicted = (np.mean(blank.astype(float)-output,axis=2)>45)&(radial<radius*.8)
        observed = glyph_mask.astype(bool)
        union = (predicted|observed).sum()
        if not union or (predicted&observed).sum()/union < max(.65,1-3/radius):
            return False
        distance = cv2.distanceTransform((~observed).astype(np.uint8),cv2.DIST_L2,3)
        exposed = (radial<radius*.85)&~cv2.dilate(observed.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)
        return bool(distance[predicted].max()<=max(1.5,radius*.035) and exposed.any()
            and np.percentile(np.max(abs(pixels[exposed]-output[exposed]),axis=1),95)<=25)

    fitted = _register(p, geometry_count, build, valid, image, render_fn, error_fn,
        'raster_bottom_stem_letter_disk_v1' if bottom_stem else 'raster_labeled_disk_v1',
        satisfactory_fn=satisfactory)
    if fitted is None:
        return None
    # Joint font pose candidates escape subpixel coordinate-descent stalls.
    # They are used only when a new stem fit fails the existing glyph check.
    for attempt in range(2 if bottom_stem else 1):
        blank = render_fn(build(fitted['parameters'], blank=True), width, height)
        if blank is None:
            return None
        output = fitted['rendered'].astype(float)
        predicted = (np.mean(blank.astype(float)-output, axis=2) > 45) & (radial < radius*.8)
        observed = glyph_mask.astype(bool)
        union = (predicted | observed).sum()
        minimum_overlap = max(.65, 1-3/radius)
        if union and (predicted & observed).sum()/union >= minimum_overlap:
            break
        if not bottom_stem or attempt:
            return None
        previous = fitted
        seed = np.asarray(previous['parameters'])
        best_loss = float(np.mean((image.astype(float)-previous['rendered'].astype(float))**2))
        extra = 0
        for dx in (-.5, 0., .5):
            for dy in (-.5, 0., .5):
                for ds in (-1., 0., 1.):
                    candidate = np.asarray(previous['parameters']).copy()
                    candidate[4:7] += (dx, dy, ds)
                    if not valid(candidate):
                        continue
                    raster = render_fn(build(candidate), width, height)
                    extra += 1
                    if raster is None:
                        continue
                    loss = float(np.mean((image.astype(float)-raster.astype(float))**2))
                    if loss < best_loss and error_fn(image, raster) <= previous['initial_error']:
                        seed, best_loss = candidate, loss
        fitted = _register(seed, geometry_count, build, valid, image,
                           render_fn, error_fn, 'raster_bottom_stem_letter_disk_v1',
                           initial_error_bound=previous['initial_error'],satisfactory_fn=satisfactory)
        if fitted is None:
            return None
        fitted['evaluations'] += previous['evaluations']+extra
    glyph_distance = cv2.distanceTransform((~observed).astype(np.uint8), cv2.DIST_L2, 3)
    if glyph_distance[predicted].max() > max(1.5, radius*.035):
        return None
    exposed = (radial < radius*.85) & ~cv2.dilate(observed.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    if not exposed.any() or np.percentile(np.max(np.abs(pixels[exposed]-output[exposed]), axis=1), 95) > 25:
        return None
    fitted['evaluations'] += semantic_evaluations
    return fitted
