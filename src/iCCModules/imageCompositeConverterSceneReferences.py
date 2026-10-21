"""Conservative, raster-grounded German references for bounded native scenes."""
from __future__ import annotations

import re

import cv2
import numpy as np

SIZE_ROLES = ('kleinere', 'grössere', 'kleinste', 'grösste', 'mittelgrosse')
POSITION_ROLES = ('linke', 'rechte', 'obere', 'untere')
COLOR_ROLES = ('rote', 'orange', 'gelbe', 'grüne', 'blaue', 'violette', 'graue', 'schwarze', 'weisse')
ROLE = '(?:'+'|'.join((*SIZE_ROLES, *POSITION_ROLES, *COLOR_ROLES))+')'
RELATION = re.compile(r'\bdie ('+ROLE+r') form liegt (vor|hinter|innerhalb|links von|rechts von|oberhalb|unterhalb) der ('+ROLE+r')(?:n)? form[.!]')


def parse_references(description):
    text = re.sub(r'\s+', ' ', str(description or '').casefold()).strip()
    relations = [m.groups() for m in RELATION.finditer(text)]
    remainder = RELATION.sub('', text)
    # Unknown predicates, negations and unrecognised/compound role phrases
    # cannot disappear through the permissive legacy shape-count grammar.
    residual = remainder.replace('jede form hat eine dunkle kontur.', '').replace('eine form liegt getrennt.', '')
    # Whole-motif scale/translation wording does not identify an object or
    # assert its relation to another object. Its actual geometry is in the raster.
    extent = r'(?:geringfügig|etwas|ein wenig|leicht)'
    residual = re.sub(r'\b(?:das (?:gesamte )?motiv|die (?:gesamte )?darstellung) ist '+extent+
                      r' (?:grösser|kleiner) dargestellt und '+extent+
                      r' nach (?:links|rechts) und (?:oben|unten) (?:versetzt|verschoben)\.', '', residual)
    if re.search(r'\b(?:form|liegt|liegen|links|rechts|oberhalb|unterhalb)\b', residual):
        return None
    if any(a == b for a, _, b in relations):
        return None
    return remainder, relations


def color_role(bgr):
    """Broad hue interiors with uncertainty gaps; colors refer to fills only."""
    # Match the rounded/clipped channels actually serialized by _hex. Search
    # parameters may temporarily leave [0, 255]; those values are not SVG colors.
    drawn = np.clip(np.rint(bgr), 0, 255)
    h, s, v = cv2.cvtColor(np.array([[drawn]], dtype=np.float32)/255., cv2.COLOR_BGR2HSV)[0, 0]
    if v < .18:
        return 'schwarze'
    if s < .12:
        return 'weisse' if v > .94 else 'graue' if .28 < v < .86 else None
    if s < .30 or v < .28:
        return None
    for role, low, high in [('orange', 20, 40), ('gelbe', 48, 68), ('grüne', 82, 158),
                            ('blaue', 202, 258), ('violette', 275, 325)]:
        if low < h < high:
            return role
    return 'rote' if h < 10 or h > 350 else None


def resolve_references(scene, relations):
    """Return only requested roles, each backed by exactly one observed object."""
    from src.iCCModules.imageCompositeConverterLayeredScene import _box
    boxes = np.array([_box(c) for c in scene])
    areas = np.prod(boxes[:, 2:]-boxes[:, :2], axis=1)
    centers = (boxes[:, 2:]+boxes[:, :2])/2
    needed = {r for a, _, b in relations for r in (a, b)}
    roles = {}
    for role in needed:
        if role in SIZE_ROLES:
            order = np.argsort(areas)
            if any(areas[b] < areas[a]*1.12 for a, b in zip(order, order[1:])):
                return None
            names = ('kleinere', 'grössere') if len(scene) == 2 else ('kleinste', 'mittelgrosse', 'grösste')
            if role not in names:
                return None
            roles[role] = int(order[names.index(role)])
        elif role in POSITION_ROLES:
            axis = 0 if role in ('linke', 'rechte') else 1
            order = np.argsort(centers[:, axis])
            if role in ('rechte', 'untere'):
                order = order[::-1]
            # A minimum three-pixel margin survives geometry refinement and
            # avoids resolving aligned or nearly aligned instances by noise.
            if abs(centers[order[1], axis]-centers[order[0], axis]) <= 3:
                return None
            roles[role] = int(order[0])
        else:
            matches = [i for i, c in enumerate(scene) if c['fill'] is not None and color_role(c['fill']) == role]
            if len(matches) != 1:
                return None
            roles[role] = matches[0]
    return roles


def position_agrees(a, relation, b):
    from src.iCCModules.imageCompositeConverterLayeredScene import _box
    ca, cb = _box(a), _box(b)
    delta = (ca[:2]+ca[2:]-cb[:2]-cb[2:])/2
    return {'links von': delta[0] < -3, 'rechts von': delta[0] > 3,
            'oberhalb': delta[1] < -3, 'unterhalb': delta[1] > 3}.get(relation, False)
