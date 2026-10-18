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
    if (letter is None or not all(t in words for t in
            ('kreisscheibe', 'einfarbig', 'dunkle', 'randkontur', 'einzelne', 'serifenlos'))
            or any(t in words for t in ('zusätzlich', 'verlauf', 'zwei buchstaben', 'ohne buchstabe', 'dreieck', 'griff', 'leitung'))
            or not re.search(r'keine anschlüsse', words)):
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
    if (not .85 < w/h < 1.18 or silhouette.sum() < .65*w*h
            or np.count_nonzero(mask & ~silhouette) > max(2, silhouette.sum()*.005)):
        return None
    contour = outline[:, 0].astype(float)+.5
    coefficients = np.linalg.lstsq(np.c_[2*contour, np.ones(len(contour))], (contour**2).sum(axis=1), rcond=None)[0]
    cx, cy = coefficients[:2]
    radius = float(np.sqrt(max(0, coefficients[2]+cx*cx+cy*cy)))
    if radius < 5 or np.mean(np.abs(np.linalg.norm(contour-[cx, cy], axis=1)-radius)) > max(.6, radius*.035):
        return None
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
        fill, dark, color = p[7:].reshape(-1, 3)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                f'<rect width="{width}" height="{height}" fill="#ffffff"/>'
                f'<circle cx="{cx:.4f}" cy="{cy:.4f}" r="{r:.4f}" fill="{_hex(fill)}" stroke="{_hex(dark)}" stroke-width="{stroke:.4f}"/>'
                + ('' if blank else f'<text x="{tx:.4f}" y="{ty:.4f}" font-family="Arial" font-weight="700" font-size="{size:.4f}" text-anchor="middle" fill="{_hex(color)}">{label}</text>')+'</svg>\n')

    p = np.r_[cx, cy, radius-.15, max(.5, radius*.09), gx+gw/2, gy+gh, gh*1.35, fill, dark, color]
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
                and np.isfinite(p).all() and np.all((p[7:] >= 0) & (p[7:] <= 255)))

    fitted = _register(p, 7, build, valid, image, render_fn, error_fn, 'raster_labeled_disk_v1')
    if fitted is None:
        return None
    # Compare the actual described font silhouette with the observed letter.
    blank = render_fn(build(fitted['parameters'], blank=True), width, height)
    if blank is None:
        return None
    output = fitted['rendered'].astype(float)
    predicted = (np.mean(blank.astype(float)-output, axis=2) > 45) & (radial < radius*.8)
    observed = glyph_mask.astype(bool)
    union = (predicted | observed).sum()
    # A three-pixel contour uncertainty matters on tiny badges, but a large
    # raster must distinguish similar letters rather than accept an OCR guess.
    minimum_overlap = max(.65, 1-3/radius)
    if not union or (predicted & observed).sum()/union < minimum_overlap:
        return None
    glyph_distance = cv2.distanceTransform((~observed).astype(np.uint8), cv2.DIST_L2, 3)
    if glyph_distance[predicted].max() > max(1.5, radius*.035):
        return None
    exposed = (radial < radius*.85) & ~cv2.dilate(observed.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    if not exposed.any() or np.percentile(np.max(np.abs(pixels[exposed]-output[exposed]), axis=1), 95) > 25:
        return None
    return fitted
