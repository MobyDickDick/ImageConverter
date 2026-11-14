"""Fit a rectangular tube with axial colour, lateral shading and two grey caps.

The bounded model has a two-stop vertical paint, a four-stop black translucent
sheen and two four-stop cap paints. All geometry and paint come from the input
raster; no reference SVG or catalogue identity participates in the fit.
"""
from __future__ import annotations

from itertools import combinations
import re
from xml.etree import ElementTree as ET

import numpy as np

from src.iCCModules.imageCompositeConverterAdaptiveSearch import current_search, pixel_quality
from src.iCCModules.imageCompositeConverterFilledSymbols import _hex
from src.iCCModules.imageCompositeConverterDescriptionLanguage import normalize_description


def tube_contract(description):
    def normalized(value):
        return re.sub(r'\s+', ' ', normalize_description(value).casefold()).strip().rstrip('.')
    text = normalized(description)
    # The workbench changes the pose of the whole motif. Consume only its
    # complete terminal sentence; other objects or changed paint still reject.
    text = re.sub(
        r'\s+(?:das (?:gesamte )?motiv|die (?:gesamte )?darstellung) ist '
        r'(?:geringfügig|etwas|ein wenig|leicht) (?:kleiner|grösser|groesser) dargestellt '
        r'und (?:geringfügig|etwas|ein wenig|leicht) nach (?:links|rechts) '
        r'und (?:oben|unten) (?:versetzt|verschoben)$', '', text).rstrip('.')
    # Consume complete known contracts, including the original terse wording.
    # Extra objects/negations must not be silently discarded by this model.
    old = ('röhre oben und unten grau; vertikaler verlauf von gelbgrün nach dunkelgrün. '
           'gesamter farbverlauf: links dunkel, mitte hell, rechts dunkel (röhreneffekt)')
    detailed = ('eine senkrechte, schmale röhre als langgezogenes rechteck ohne randkontur. '
        'oben und unten schließt jeweils eine flache, graue rechteckige kappe bündig mit dem röhrenkörper ab. '
        'zwischen den kappen verläuft die grundfarbe senkrecht von gelbgrün oben nach dunkelgrün unten. '
        'ein zusätzlicher waagerechter helligkeitsverlauf erzeugt den röhreneffekt: links dunkel, '
        'etwas rechts der mitte ein heller glanzbereich, zum rechten rand wieder dunkler. '
        'auch die grauen kappen haben diesen seitlichen glanzverlauf. keine schriftzeichen und keine weiteren objekte')
    return text in {normalized(old), normalized(detailed)}


def _piecewise_profile(profile, coordinates):
    """Four stops, two free interior knots; work is independent of image size."""
    def fit(knots):
        basis = np.column_stack([np.interp(coordinates, knots, row) for row in np.eye(4)])
        colors = np.linalg.lstsq(basis, profile, rcond=None)[0]
        score = float(np.mean((basis @ colors-profile)**2))
        return score, np.asarray(knots), colors
    best = min((fit([0., a, b, 1.]) for a, b in combinations(np.linspace(.05, .95, 19), 2)),
               key=lambda item: item[0])
    for step in (.02, .005, .001):
        _, knots, _ = best
        for a in knots[1]+np.arange(-2, 3)*step:
            for b in knots[2]+np.arange(-2, 3)*step:
                if .01 <= a < b-.01 and b <= .99:
                    candidate = fit([0., a, b, 1.])
                    if candidate[0] < best[0]:
                        best = candidate
    return best[1:]


def tube_details(reference, rendered, bounds, caps):
    """Local checks preserve both caps and both paint axes, even on small caps."""
    x, y, X, Y = map(int, bounds)
    top, bottom = map(int, caps)
    regions = [(y, top), (top+2, bottom-2), (bottom, Y)]
    errors = []
    for a, b in regions:
        if b-a < 2:
            return dict(passed=False)
        delta = abs(reference[a:b, x:X].astype(float)-rendered[a:b, x:X].astype(float))
        errors.append(float(np.percentile(delta, 95)))
    return dict(region_error_p95=errors, passed=bool(max(errors) <= 8))


def validate_tube_refinement(result, image, registration):
    """Recheck this model after generic native-vector parameter polishing."""
    try:
        root = ET.fromstring(result['svg'])
        shapes = [e for e in root.iter() if e.tag.rsplit('}', 1)[-1] in
                  {'rect', 'circle', 'ellipse', 'path', 'line', 'polygon', 'polyline', 'image', 'text', 'use'}]
        if (len(shapes) != 4 or any(e.tag.rsplit('}', 1)[-1] != 'rect' for e in shapes)
                or {e.get('fill') for e in shapes} !=
                   {'url(#tubeColor)', 'url(#tubeShade)', 'url(#cap0)', 'url(#cap1)'}
                or any(e.get('stroke', 'none') != 'none' for e in shapes)):
            return False
        quality = pixel_quality(image, result['rendered'])
        details = tube_details(image, result['rendered'], registration['parameters']['bounds'],
                               registration['parameters']['caps'])
        return bool(quality and quality['passed'] and details['passed'])
    except (ET.ParseError, KeyError, TypeError, ValueError):
        return False


def fit_gradient_tube(width, height, *, description, image, render_fn, error_fn):
    arr = np.asarray(image)
    session = current_search()
    if (not tube_contract(description) or arr.shape != (height, width, 3)
            or min(width, height) < 12 or not np.isfinite(arr).all()
            or (session and session.time_reason())):
        return None
    pixels = arr.astype(float)
    yy, xx = np.nonzero(pixels.min(axis=2) < 240)
    if len(xx) < 100:
        return None
    x, X, y, Y = int(xx.min()), int(xx.max())+1, int(yy.min()), int(yy.max())+1
    if Y-y < 2*(X-x) or X-x < 12:
        return None
    core = pixels[y:Y, x:X]
    chroma = np.median(np.ptp(core, axis=2), axis=1)
    rows = np.flatnonzero(chroma > 20)
    if not len(rows):
        return None
    # At a fractional outside edge the cap blends with the coloured body below
    # it. Isolated chromatic edge rows are not the axial body interval.
    rows = max(np.split(rows, np.flatnonzero(np.diff(rows) > 1)+1), key=len)
    top, bottom = y+int(rows[0]), y+int(rows[-1])+1
    if (min(top-y, Y-bottom) < 2 or max(top-y, Y-bottom) > (Y-y)*.2
            or bottom-top < 12 or np.any(chroma[top-y+2:bottom-y-2] <= 20)):
        return None
    # Ignore JPEG ringing around the cap/body junctions and rectangle edges.
    body = pixels[top+2:bottom-2, x+1:X-1]
    cap_profiles = []
    for a, b in ((y, top), (bottom, Y)):
        inset = 1 if b-a >= 4 else 0
        cap_profiles.append(np.median(pixels[a+inset:b-inset, x+1:X-1], axis=0))
    if max(np.ptp(profile, axis=1).max() for profile in cap_profiles) > 12:
        return None
    # Rank-one lateral shading: the same factor multiplies every row/channel.
    # Using the mean avoids a costly resolution-dependent matrix decomposition.
    shade = body.mean(axis=(0, 2))
    shade /= shade.max()
    t = (np.arange(x+1, X-1)+.5-x)/(X-x)
    knots, values = _piecewise_profile(shade[:, None], t)
    values = np.clip(values[:, 0], 0., 1.)
    factor = np.interp(t, knots, values)
    if (factor.min() < .25 or min(factor.max()-factor[0], factor.max()-factor[-1]) < .08
            or not .3 < t[np.argmax(factor)] < .85):
        return None
    profile = np.median(body/factor[None, :, None], axis=1)
    vertical = (np.arange(top+2, bottom-2)+.5-top)/(bottom-top)
    basis = np.c_[1-vertical, vertical]
    colors = np.linalg.lstsq(basis, profile, rcond=None)[0]
    if np.any(colors < 0) or np.any(colors > 255):
        return None
    # Require the described yellow-green to darker green transition in BGR.
    blue, green, red = colors.T
    if not (red[0] > blue[0]+25 and green[0] > blue[0]+25 and
            green[1] > red[1]+20 and green[1] > blue[1]+15 and
            colors[0].mean() > colors[1].mean()+10):
        return None
    predicted = (basis @ colors)[:, None, :]*factor[None, :, None]
    if np.percentile(abs(body-predicted), 95) > 6:
        return None
    cap_paints = [_piecewise_profile(profile, t) for profile in cap_profiles]

    # A resized JPEG can blend a cap junction across a pixel. Recover that
    # coverage from both observed paints instead of snapping the cap to a row.
    full_t = (np.arange(X-x)+.5)/(X-x)
    full_factor = np.interp(full_t, knots, values)
    boundaries = []
    for i, boundary in enumerate((top, bottom)):
        sample_rows = np.arange(boundary-1, boundary+2)
        end_color = colors[i][None, :]*full_factor[:, None]
        ck, cc = cap_paints[i]
        cap_color = np.column_stack([np.interp(full_t, ck, cc[:, c]) for c in range(3)])
        scores = []
        for proposal in np.linspace(boundary-1, boundary+1, 81):
            coverage = np.clip(sample_rows+1-proposal if i == 0 else proposal-sample_rows, 0, 1)
            prediction = coverage[:, None, None]*end_color+(1-coverage[:, None, None])*cap_color
            score = np.mean((pixels[sample_rows, x:X]-prediction)**2)
            scores.append((float(score), float(proposal)))
        boundaries.append(min(scores)[1])
    top_edge, bottom_edge = boundaries

    def paint(name, offsets, paint_colors, vertical=False, opacity=None):
        coords = f'x1="0" x2="0" y1="{top_edge:.8g}" y2="{bottom_edge:.8g}"' if vertical else f'x1="{x}" x2="{X}" y1="0" y2="0"'
        stops = ''.join(f'<stop offset="{offset:.8g}" stop-color="{_hex(color)}"'+
                        (f' stop-opacity="{opacity[i]:.8g}"' if opacity is not None else '')+'/>'
                        for i, (offset, color) in enumerate(zip(offsets, paint_colors)))
        return f'<linearGradient id="{name}" gradientUnits="userSpaceOnUse" {coords}>{stops}</linearGradient>'

    definitions = paint('tubeColor', [0., 1.], colors, vertical=True)
    definitions += paint('tubeShade', knots, np.zeros((4, 3)), opacity=1-values)
    for i, (cap_knots, cap_colors) in enumerate(cap_paints):
        definitions += paint(f'cap{i}', cap_knots, np.clip(cap_colors, 0, 255))
    def build(geometry):
        left, upper, right, lower, cap_top, cap_bottom = geometry
        def rectangle(a, b, fill):
            return (f'<rect x="{left:.8g}" y="{a:.8g}" width="{right-left:.8g}" '
                    f'height="{b-a:.8g}" fill="url(#{fill})" stroke="none"/>')
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                f'<defs>{definitions}</defs>'+rectangle(upper, lower, 'tubeColor')+
                rectangle(upper, lower, 'tubeShade')+rectangle(upper, cap_top, 'cap0')+
                rectangle(cap_bottom, lower, 'cap1')+'</svg>')

    geometry = np.array([x, y, X, Y, top_edge, bottom_edge], dtype=float)
    svg = build(geometry)
    if session and session.time_reason():
        return None
    rendered = render_fn(svg, width, height)
    evaluations = 1
    if session:
        session.evaluations += 1
    if rendered is None:
        return None
    initial_error = float(error_fn(arr, rendered))
    loss = float(np.mean((pixels-rendered)**2))
    # Integer foreground bounds are only an initializer: transformed tubes have
    # fractional outside edges as well as fractional cap junctions. Fit those
    # six edges against actual rendered candidates, preserving the four paints.
    seen = {tuple(geometry)}
    if loss > 1:
        origin = geometry.copy()
        for step in (.5, .25, .125, .0625):
            for _ in range(2):
                improved = False
                for index in range(6):
                    anchor = geometry.copy()
                    # Layered antialiasing need not have a monotone loss within
                    # one edge pixel; sample across that pixel at coarse scale.
                    for direction in ((-2, -1.5, -1, -.5, .5, 1, 1.5, 2) if step == .5 else (-1, 1)):
                        proposal = anchor.copy()
                        proposal[index] += direction*step
                        key = tuple(proposal)
                        if key in seen or np.max(abs(proposal-origin)) > 1.5:
                            continue
                        seen.add(key)
                        left, upper, right, lower, cap_top, cap_bottom = proposal
                        if not (0 <= left < right <= width and 0 <= upper < cap_top < cap_bottom < lower <= height):
                            continue
                        if session and session.time_reason():
                            return None
                        candidate = build(proposal)
                        measured = render_fn(candidate, width, height)
                        evaluations += 1
                        if session:
                            session.evaluations += 1
                        if measured is None:
                            continue
                        candidate_loss = float(np.mean((pixels-measured)**2))
                        if candidate_loss < loss:
                            geometry, svg, rendered, loss = proposal, candidate, measured, candidate_loss
                            improved = True
                if not improved:
                    break
    quality = pixel_quality(arr, rendered)
    details = tube_details(arr, rendered, [x, y, X, Y], [top, bottom])
    if not quality['passed'] or not details['passed']:
        return None
    error = float(error_fn(arr, rendered))
    return dict(svg=svg, rendered=rendered, error=error, initial_error=initial_error,
                source='gradient_tube', evaluations=evaluations, quality=quality, details=details,
                parameters=dict(bounds=geometry[:4].tolist(), caps=geometry[4:].tolist(),
                                shade_knots=knots.tolist(), shade=values.tolist(), colors=colors.tolist()))
