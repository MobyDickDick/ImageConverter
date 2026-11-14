"""Fit a single unlabelled, flat-filled circle from its observed rim.

Thin rings must not require a solid foreground core: on tiny JPEGs only the
outline crosses the foreground threshold. Emit one native circle, never paths.
"""
from __future__ import annotations

import re

import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterAdaptiveSearch import pixel_quality
from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _image, _register
from src.iCCModules.imageCompositeConverterPrimitiveScene import _circle


_COLOR = r'(?:(?:hell|dunkel)?(?:grau|grün|gruen|blau|rot|gelb|braun|rosa|violett|schwarz|weiß|weiss)(?:e[nrms]?)?)'
_DESCRIPTION = re.compile(
    rf'(?:ein\s+)?(?:(?:einfacher|unbeschrifteter)\s+)?(?:{_COLOR}\s+)?kreis'
    rf'(?:\s+mit\s+(?:{_COLOR}\s+)?(?:rand|kontur|umrandung)'
    rf'(?:\s+und\s+{_COLOR}\s+(?:hintergrund|füllung|fuellung))?)?'
    r'\.?'
    rf'(?:\s*(?:(?:keine beschriftung|keine schriftzeichen|ohne text|keine anschlüsse|ohne anschluss)'
    rf'\.?|hintergrund:\s*{_COLOR}\.?)){{0,3}}'
    # Whole-motif pose/scale wording adds no objects. Keep the full match so
    # labels or attachments before/after this sentence still reject the model.
    # Geometry continues to come from pixels, never from these relative words.
    r'(?:\s+(?:das (?:gesamte )?motiv|die (?:gesamte )?darstellung) ist '
    r'(?:geringfügig|etwas|ein wenig|leicht) (?:kleiner|grösser|groesser) dargestellt '
    r'und (?:geringfügig|etwas|ein wenig|leicht) nach (?:links|rechts) '
    r'und (?:oben|unten) (?:versetzt|verschoben)\.)?'
)


def fit_plain_disk(width, height, *, description, image, render_fn, error_fn):
    # Full matching keeps labels, attachments, gradients and additional objects
    # out of this model even when they occupy too few pixels for global gates.
    text = ' '.join(str(description or '').casefold().split())
    if not _DESCRIPTION.fullmatch(text):
        return None
    pixels = _image(width, height, image)
    if pixels is None:
        return None
    border = np.concatenate((pixels[0], pixels[-1], pixels[:, 0], pixels[:, -1]))
    background = np.median(border, axis=0)
    mask = (np.max(abs(pixels-background), axis=2) > 25).astype('uint8')
    contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]
    if not contours:
        return None
    outline = max(contours, key=cv2.contourArea)
    center, outer_radius, residual = _circle(outline)
    x, y, w, h = cv2.boundingRect(outline)
    if (outer_radius < 4 or abs(w-h) > max(2, .06*max(w, h))
            or residual > max(.4, outer_radius*.025)):
        return None
    yy, xx = np.indices((height, width), dtype=float)
    radial = np.hypot(xx+.5-center[0], yy+.5-center[1])
    core = radial < outer_radius*.6
    if core.sum() < 8:
        return None
    fill = np.median(pixels[core], axis=0)
    # Explicit local checks prevent small glyphs or outside attachments from
    # being silently lost in an otherwise good whole-image circle fit.
    if np.max(abs(pixels[core]-fill)) > 25:
        return None
    annulus = (radial > outer_radius*.8) & (radial < outer_radius+1)
    rim = np.percentile(pixels[annulus], 10, axis=0)
    if np.mean(fill-rim) < 15:
        return None
    radius = outer_radius-.4
    stroke_width = max(.7, outer_radius*.07)
    parameters = np.r_[center, radius, stroke_width, fill, rim, background]

    def build(p):
        cx, cy, r, sw = p[:4]
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
                f'viewBox="0 0 {width} {height}">'
                f'<rect width="{width}" height="{height}" fill="{_hex(p[10:13])}"/>'
                f'<circle cx="{cx:.4f}" cy="{cy:.4f}" r="{r:.4f}" '
                f'stroke-width="{sw:.4f}" fill="{_hex(p[4:7])}" stroke="{_hex(p[7:10])}"/></svg>')

    def valid(p):
        cx, cy, r, sw = p[:4]
        return (r >= 3 and .4 <= sw <= r*.3
                and r+sw/2 <= min(cx, cy, width-cx, height-cy)+.5
                and np.linalg.norm(p[:2]-center) <= 2
                and abs(r-radius) <= 2 and np.all((p[4:] >= 0) & (p[4:] <= 255)))

    def details(p, rendered):
        distance = np.hypot(xx+.5-p[0], yy+.5-p[1])
        exposed = (distance < p[2]-p[3]/2-1.5) | (distance > p[2]+p[3]/2+1.5)
        return bool(exposed.any() and np.max(abs(pixels[exposed]-rendered[exposed])) <= 25)

    fitted = _register(parameters, 4, build, valid, image, render_fn, error_fn,
                       'plain_disk_v1', satisfactory_fn=lambda p, measured: details(p, measured[3]))
    if fitted is None:
        return None
    quality = pixel_quality(image, fitted['rendered'])
    if not quality or not quality['passed'] or not details(fitted['parameters'], fitted['rendered']):
        return None
    fitted['quality'] = quality
    return fitted
