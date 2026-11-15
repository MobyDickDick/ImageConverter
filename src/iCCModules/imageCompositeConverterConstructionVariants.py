"""Seeded, bounded changes that ordinary color/width descent cannot express."""
from __future__ import annotations

import copy
import hashlib
import random
from xml.etree import ElementTree as ET

import numpy as np

from src.iCCModules.imageCompositeConverterSearchPortfolio import settings

NS = 'http://www.w3.org/2000/svg'


def construction_variants(svg, image, rendered, session):
    root = ET.fromstring(svg)
    h, w = image.shape[:2]
    proposals = []
    # Paint-axis changes are discrete alternatives, not stop-color tweaks.
    for index, node in enumerate(root.iter()):
        if node.tag.rsplit('}', 1)[-1] != 'linearGradient' or node.get('href') or node.get('gradientTransform'):
            continue
        candidate = copy.deepcopy(root)
        gradient = list(candidate.iter())[index]
        user = gradient.get('gradientUnits') == 'userSpaceOnUse'
        for key in ('x1', 'x2', 'y1', 'y2'):
            gradient.attrib.pop(key, None)
        x1, x2 = node.get('x1', '0%'), node.get('x2', '100%')
        y1, y2 = node.get('y1', '0%'), node.get('y2', '0%')
        vertical = x1 == x2 and y1 != y2
        if vertical:
            gradient.set('x1', '0' if user else '0%')
            gradient.set('x2', str(w) if user else '100%')
            gradient.set('y1', '0')
            gradient.set('y2', '0')
        else:
            gradient.set('x1', '0')
            gradient.set('x2', '0')
            gradient.set('y1', '0' if user else '0%')
            gradient.set('y2', str(h) if user else '100%')
        proposals.append((ET.tostring(candidate, encoding='unicode'), 'gradient_axis:'+str(index)))

    # Register x/y extent independently. A uniform scale cannot repair a bad
    # aspect ratio, even after thousands of successful local parameter steps.
    def bounds(raster):
        a = raster.astype(float)
        background = np.median(np.concatenate((a[0], a[-1], a[:, 0], a[:, -1])), axis=0)
        ys, xs = np.nonzero(np.max(abs(a-background), axis=2) > 25)
        return (xs.min(), ys.min(), xs.max()+1, ys.max()+1) if len(xs) >= 4 else None

    observed, predicted = bounds(image), bounds(rendered)
    if observed and predicted:
        x, y, X, Y = observed
        a, b, A, B = predicted
        sx, sy = (X-x)/(A-a), (Y-y)/(B-b)
        if .25 <= sx <= 4 and .25 <= sy <= 4:
            for scale_x, scale_y, label in ((sx, sy, 'both'), (sx, 1., 'width'), (1., sy, 'height')):
                if abs(scale_x-1)+abs(scale_y-1) < .01:
                    continue
                candidate = copy.deepcopy(root)
                wrapper = ET.Element(f'{{{NS}}}g', transform=(
                    f'translate({x-a*scale_x:.6f} {y-b*scale_y:.6f}) scale({scale_x:.6f} {scale_y:.6f})'))
                for child in list(candidate):
                    if child.tag.rsplit('}', 1)[-1] not in {'defs', 'style', 'title', 'desc', 'metadata'}:
                        candidate.remove(child)
                        wrapper.append(child)
                candidate.append(wrapper)
                proposals.append((ET.tostring(candidate, encoding='unicode'), 'raster_bounds:'+label))

    # Correct near-horizontal/vertical strokes as a construction, preserving
    # their midpoint. Endpoint descent currently has no access to these values.
    candidate, changes = copy.deepcopy(root), 0
    for node in candidate.iter():
        if node.tag.rsplit('}', 1)[-1] != 'line':
            continue
        try:
            x1, y1, x2, y2 = (float(node.get(key, '0')) for key in ('x1', 'y1', 'x2', 'y2'))
        except ValueError:
            continue
        dx, dy = abs(x2-x1), abs(y2-y1)
        if 0 < dy < dx*.2:
            node.set('y1', str((y1+y2)/2))
            node.set('y2', str((y1+y2)/2))
            changes += 1
        elif 0 < dx < dy*.2:
            node.set('x1', str((x1+x2)/2))
            node.set('x2', str((x1+x2)/2))
            changes += 1
    if changes:
        proposals.append((ET.tostring(candidate, encoding='unicode'), 'aligned_lines'))

    round_number = getattr(session, 'construction_round', 0)
    session.construction_round = round_number+1
    random.Random((settings() or {}).get('seed', 0)+round_number).shuffle(proposals)
    seen = getattr(session, 'construction_trials', None)
    if seen is None:
        seen = session.construction_trials = set()
    for candidate, label in proposals:
        identity = hashlib.sha256(candidate.encode()).digest()
        if identity not in seen:
            seen.add(identity)
            yield candidate, 'construction_variant:'+label
