"""Description-based object limits and native representation simplification.

Simplicity is a shared selection preference, never a reason to pass bad pixels.
Analytic replacements are proposals: callers must render them against the source.
"""
from __future__ import annotations

import copy
import re
from xml.etree import ElementTree as ET

import cv2
import numpy as np

DRAW = {'line', 'rect', 'circle', 'ellipse', 'polygon', 'polyline', 'path', 'text'}
EXCLUDED = {'defs', 'clipPath', 'mask', 'marker', 'pattern', 'symbol', 'metadata'}
NUMBER = r'[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?'
# SVG coordinates may be rounded when serialized. This is a numerical
# tolerance, not permission to deform a named geometric primitive.
FORM_TOLERANCE = 1e-5


def straight_strip(vertices):
    """A clipped straight band has two parallel sides and straight end cuts."""
    if not cv2.isContourConvex(vertices.astype(np.float32)):
        return False
    edges = np.roll(vertices, -1, axis=0)-vertices
    lengths = np.linalg.norm(edges, axis=1)
    if min(lengths) <= 0:
        return False
    directions = edges/lengths[:, None]
    longest = np.argsort(lengths)[-2:]
    cross = lambda a, b: a[..., 0]*b[..., 1]-a[..., 1]*b[..., 0]
    if abs(cross(*directions[longest])) > FORM_TOLERANCE:
        return False
    # Caps follow the two orthogonal axes of a clipping rectangle, including
    # a rotated one. An unclipped band's two caps are parallel as well.
    other = np.delete(directions, longest, axis=0)
    return bool(np.all((abs(cross(other,other[0])) < FORM_TOLERANCE)
                       | (abs(other @ other[0]) < FORM_TOLERANCE)))


def drawing_nodes(root, path=()):
    for index, node in enumerate(root):
        tag = node.tag.rsplit('}', 1)[-1]
        if tag in EXCLUDED or node.get('display') == 'none':
            continue
        if tag in DRAW:
            yield path+(index,), node
        yield from drawing_nodes(node, path+(index,))


def representation_cost(svg):
    """Charge every shape and its geometric degrees of freedom, regardless of class."""
    nodes = list(drawing_nodes(ET.fromstring(svg)))
    controls = 0
    for _, node in nodes:
        for key in ('d', 'points', 'x', 'y', 'cx', 'cy', 'r', 'rx', 'ry', 'x1', 'y1', 'x2', 'y2', 'width', 'height'):
            controls += len(re.findall(NUMBER, node.get(key, '')))
    generic = sum(n.tag.rsplit('}', 1)[-1] in {'path', 'polyline'} for _, n in nodes)
    return dict(elements=len(nodes), coordinates=controls,
                penalty=len(nodes)*.00005+controls*.000002+generic*.000005)


def description_object_limits(text):
    from src.iCCModules.imageCompositeConverterPartitionedRhombus import partitioned_rhombus_spec, partition_inventory
    partition = partitioned_rhombus_spec(text)
    if partition:
        return partition_inventory(partition)
    from src.iCCModules.imageCompositeConverterThreeWingValve import three_wing_valve_spec
    if three_wing_valve_spec(text):
        return dict(triangle=3, line=1, square=1, diagonal=2)
    from src.iCCModules.imageCompositeConverterTwoWayValve import two_way_valve_spec
    valve = two_way_valve_spec(text)
    if valve:
        return (dict(square=1, diagonal=2, line=1, triangle=2) if valve['motor']=='square'
                else dict(circle=1, line=1, triangle=2))
    words = re.sub(r'"[^"\n]*"|„[^“\n]*“', '', text).casefold()
    numbers = dict(ein=1, eine=1, einen=1, einem=1, einer=1, eins=1, zwei=2, drei=3, vier=4,
                   fünf=5, sechs=6, sieben=7, acht=8, neun=9, zehn=10, beide=2, beiden=2)
    count = r'('+ '|'.join(numbers)+r'|[0-9]+)'
    adjective = (r'(?:(?:gerad|horizontal|vertikal|waagerecht|waagrecht|senkrecht|diagonal|'
                 r'grau|dunkelgrau|hellgrau|rot|blau|grün|gelb|weiss|weiß|schwarz|'
                 r'durchgehend|gestrichelt|dünn|schmal|breit|klein|gross|groß|ungefüllt|gefüllt|'
                 r'ganz|sehr|hochkantig|hoh|lang)[enrms]*[,\s]+|'
                 r'[a-zäöüß-]+(?:en|er|es|em|e)[,\s]+){0,6}')
    noun = r'(kreis(?:e[n]?)?|rechteck(?:e[n]?)?|quadrat(?:e[n]?)?|rauten?|ellipsen?|dreieck(?:e[n]?)?|geraden?|linien?|diagonalen?|striche?)'
    limits, covered = {}, []
    for match in re.finditer(r'\b'+count+r'\s+'+adjective+noun+r'\b', words):
        number, form = match.groups()
        covered.append(match.span())
        if re.search(r'\b(?:ohne|nicht|kein[enrms]?)\s*$', words[:match.start()]):
            continue
        # "geraden Rand" is an adjective, not a described straight object.
        if form.startswith('gerad') and re.match(r'\s+(?:rand|kanten?|seiten?|linien?)\b', words[match.end():]):
            continue
        if number in {'beide', 'beiden'} and re.search(r'\bmit\s*$', words[:match.start()]):
            continue  # a referenced component of an unnamed composite, not all scene strokes
        kind = ('circle' if form.startswith('kreis') else 'rect' if form.startswith('rechteck')
                else 'square' if form.startswith('quadrat') else 'diagonal' if form.startswith('diagonale')
                else 'ellipse' if form.startswith('ellipse') else 'triangle' if form.startswith('dreieck')
                else 'rhombus' if form.startswith('raute') else 'line')
        value = int(number) if number.isdigit() else numbers[number]
        if number in {'beide', 'beiden'} or re.search(r'\b(?:die|diese|der|den|des|dieser|diesen)\s*$', words[:match.start()]):
            limits[kind] = max(limits.get(kind, 0), value)
        else:
            limits[kind] = limits.get(kind, 0)+value
    bare = (r'\b(?:(?:horizontal|vertikal|waagerecht|senkrecht|grau|dunkelgrau|hellgrau|rot|blau|grün|gelb|'
            r'weiss|weiß|schwarz)[enrms]*\s+)+'+noun+r'\b')
    seen = set()
    for match in re.finditer(bare, words):
        if any(start <= match.start() < end for start, end in covered) or match[0] in seen:
            continue
        covered.append(match.span())
        if re.search(r'\b(?:ohne|kein[enrms]?)\s*$', words[:match.start()]):
            continue
        form = match[1]
        kind = ('circle' if form.startswith('kreis') else 'rect' if form.startswith('rechteck')
                else 'square' if form.startswith('quadrat') else 'diagonal' if form.startswith('diagonale')
                else 'ellipse' if form.startswith('ellipse') else 'triangle' if form.startswith('dreieck')
                else 'rhombus' if form.startswith('raute') else 'line')
        if kind in limits and re.search(
                r'\b(?:(?:die|der|das|diese[nrms]?)\s+(?:(?:link|recht|ober|unter|vertikal|horizontal)[enrms]*\s+)*|(?:link|recht|ober|unter)[enrms]+\s+)$',
                words[:match.start()]):
            continue  # a definite reference describes an already counted instance
        limits[kind] = limits.get(kind, 0)+1
        seen.add(match[0])
    # A singular noun also declares an instance without an article, e.g.
    # "Pumpensymbol: Kreis mit einem gefüllten Dreieck". Later references to
    # the same singular shape do not create additional objects.
    for form, kind in (('kreis', 'circle'), ('rechteck', 'rect'), ('quadrat', 'square'),
                       ('raute', 'rhombus'), ('ellipse', 'ellipse'), ('dreieck', 'triangle'),
                       ('gerade', 'line'), ('linie', 'line')):
        for match in re.finditer(r'\b'+form+r'\b', words):
            if any(start <= match.start() < end for start, end in covered):
                continue
            if re.search(r'\b(?:ohne|kein[enrms]?)\s+'+adjective+r'$', words[:match.start()]):
                continue
            if form == 'gerade' and re.match(r'\s+(?:rand|kanten?|seiten?|linien?)\b', words[match.end():]):
                continue
            limits.setdefault(kind, 1)
    if not limits and words.strip(' .\n') in {'gerade', 'linie', 'kreis', 'rechteck', 'ellipse', 'dreieck'}:
        limits[dict(gerade='line', linie='line', kreis='circle', rechteck='rect', ellipse='ellipse', dreieck='triangle')[words.strip(' .\n')]] = 1
    # Rectangles and their special cases have two diagonals. "mit Diagonalen"
    # is a complete component claim even without spelling out "zwei".
    if any(limits.get(kind) for kind in ('rect', 'square', 'rhombus')) and 'diagonal' not in limits:
        if re.search(r'\bmit\s+(?:beiden\s+|den\s+)?diagonalen\b', words):
            limits['diagonal'] = 2
    # Composite vocabulary expands once; references to the same handle are not
    # additional scene objects. A Kelle is a circular head and a straight stem.
    if (re.search(r'(?<!keine )\bkelle\b', words) and re.search(r'\bgriff\b', words)
            and not re.search(r'\b(?:kein[enrms]?|ohne)\s+(?:eine?\s+)?kelle\b', words)):
        limits['circle'] = max(1, limits.get('circle', 0))
        limits['line'] = max(1, limits.get('line', 0))
    return limits


def complete_object_list(text):
    """Only self-contained lists declare absence of all other object classes."""
    words = re.sub(r'"[^"\n]*"|„[^“\n]*“', '', text).casefold().strip()
    words = re.sub(r'^\s*(?:das (?:bild|motiv) enthält|es gibt)\s+(?:genau\s+)?', '', words)
    term = (r'\b(?:ein(?:e[nmr]?)?|eins|zwei|drei|vier|fünf|sechs|[0-9]+)\s+(?:\w+\s+){0,5}?'
            r'(?:kreise?|rechtecke?|quadrate?|rauten?|ellipsen?|dreiecke?|geraden?|linien?|diagonalen?|striche?)\b')
    rest, count = re.subn(term, '', words)
    return bool(count and not re.sub(r'\b(?:und|sowie)\b|[\s,.;]', '', rest))


def path_points(node):
    """Read linear SVG subpaths; curves stay curves and are never guessed straight."""
    tag = node.tag.rsplit('}', 1)[-1]
    if tag in {'polygon', 'polyline'}:
        values = list(map(float, re.findall(NUMBER, node.get('points', ''))))
        if len(values) < 4 or len(values) % 2:
            return []
        return [(np.array(values).reshape(-1, 2), tag == 'polygon')]
    if tag != 'path':
        return []
    data = node.get('d', '')
    if re.search(r'[^MLHVZmlhvz\s,]', re.sub(NUMBER, '', data)):
        return []
    tokens = re.findall(r'[MLHVZmlhvz]|'+NUMBER, data)
    if re.sub(r'[MLHVZmlhvz\s,]|'+NUMBER, '', data):
        return []
    paths, points, current = [], [], np.zeros(2)
    index, command = 0, None
    try:
        while index < len(tokens):
            if tokens[index].isalpha():
                command = tokens[index]
                index += 1
                if command.upper() == 'Z':
                    if points:
                        paths.append((np.array(points), True))
                        current = np.array(points[0])
                    points, command = [], None
                    continue
            if command is None:
                return []
            kind = command.upper()
            if kind in {'M', 'L'}:
                xy = np.array([float(tokens[index]), float(tokens[index+1])])
                index += 2
                if command.islower():
                    xy += current
                if kind == 'M':
                    if points:
                        paths.append((np.array(points), False))
                    points = []
                    command = 'l' if command.islower() else 'L'
            elif kind in {'H', 'V'}:
                xy = current.copy()
                axis = 0 if kind == 'H' else 1
                xy[axis] = float(tokens[index])+(current[axis] if command.islower() else 0)
                index += 1
            else:
                return []
            current = xy
            points.append(xy.copy())
        if points:
            paths.append((np.array(points), False))
    except (ValueError, IndexError):
        return []
    return paths


def _vertices(points, closed, epsilon=.01):
    if not np.isfinite(points).all():
        return points
    return cv2.approxPolyDP(points.astype(np.float32).reshape(-1, 1, 2), epsilon, closed)[:, 0].astype(float)


def logical_inventory(svg, limits, symbol_strokes=0):
    root = ET.fromstring(svg)
    inventory = dict.fromkeys(limits, 0)
    viewport_matrix = np.eye(2)
    try:
        view = list(map(float, re.split(r'[\s,]+', root.get('viewBox', '').strip()))) if root.get('viewBox') else [0., 0., float(root.get('width', 0)), float(root.get('height', 0))]
        vx, vy, vw, vh = view
        if root.get('preserveAspectRatio','').strip() == 'none' and root.get('viewBox'):
            def viewport_length(key, default):
                value = root.get(key,str(default))
                if not re.fullmatch(NUMBER+r'(?:px)?',value.strip()):
                    raise ValueError('unsupported viewport length')
                return float(value.removesuffix('px'))
            w,h = viewport_length('width',vw),viewport_length('height',vh)
            if not np.isfinite([w,h,vw,vh]).all() or min(w,h,vw,vh) <= 0:
                raise ValueError('invalid viewport')
            # Only the anisotropy matters to form identity. Keeping unit area
            # also preserves the inventory's existing paint-area comparisons.
            ratio = np.sqrt((w/vw)/(h/vh))
            viewport_matrix = np.diag([ratio,1/ratio])
            vx,vy,vw,vh = vx*ratio,vy/ratio,vw*ratio,vh/ratio
        area, narrow = vw*vh, max(3., max(vw, vh)*.025)
    except ValueError:
        vx, vy, vw, vh, area, narrow = 0., 0., 0., 0., 0., 3.
    fields = {}
    for _, n in drawing_nodes(root):
        if n.tag.rsplit('}', 1)[-1] == 'rect' and n.get('fill', 'none') != 'none':
            try:
                fields[n.get('fill')] = max(fields.get(n.get('fill'), 0), float(n.get('width', 0))*float(n.get('height', 0)))
            except ValueError:
                pass
    rectangles = {}
    visible = list(drawing_nodes(root))
    substantial_rectangles = 0
    for _, n in visible:
        if n.tag.rsplit('}', 1)[-1] == 'rect':
            try:
                substantial_rectangles += min(float(n.get('width', 0)), float(n.get('height', 0))) > narrow
            except ValueError:
                pass
    foreground_count = sum(not (n.tag.rsplit('}', 1)[-1] == 'rect' and n.get('fill', '').lower() in {'white', '#fff', '#ffffff'}
        and n.get('width') == root.get('width') and n.get('height') == root.get('height')) for _, n in visible)
    def stroke_kind(direction):
        return 'diagonal' if 'diagonal' in limits and min(abs(direction)) > 1e-6 else 'line'
    def displayed_matrix(location, node):
        from src.iCCModules.imageCompositeConverterArrowAssertions import _compose, _transform
        parent, transforms = root, [root.get('transform', '')]
        for index in location[:-1]:
            parent = parent[index]
            transforms.append(parent.get('transform', ''))
        matrix = (1., 0., 0., 1., 0., 0.)
        for value in transforms+[node.get('transform', '')]:
            matrix = _compose(matrix, _transform(value))
        a, b, c, d, tx, ty = matrix
        return viewport_matrix @ np.array([[a, c], [b, d]]), viewport_matrix @ np.array([tx, ty])
    for location, node in drawing_nodes(root):
        tag = node.tag.rsplit('}', 1)[-1]
        # A leading neutral backing cannot paint anything on the white canvas,
        # even when a reference variation transforms it away from the edges.
        # Later white rectangles can mask foreground and remain real objects.
        if (visible and node is visible[0][1] and tag == 'rect'
                and node.get('fill', '').lower() in {'white', '#fff', '#ffffff'}
                and node.get('stroke', 'none') == 'none'):
            continue
        kind = tag
        matrix, translation = displayed_matrix(location, node)
        if tag in {'circle', 'ellipse'}:
            try:
                radii = ([float(node.get('r', 0))]*2 if tag == 'circle'
                         else [float(node.get('rx', 0)), float(node.get('ry', 0))])
                center = [float(node.get('cx',0)),float(node.get('cy',0))]
                if not np.isfinite(radii+center).all() or min(radii) <= 0:
                    continue
                axes = np.linalg.svd(matrix @ np.diag(radii), compute_uv=False)
                if not np.isfinite(axes).all() or min(axes) <= 0:
                    continue
                kind = 'circle' if min(axes) > 0 and max(axes)-min(axes) < max(axes)*FORM_TOLERANCE else 'ellipse'
            except ValueError:
                continue
        if tag == 'line':
            try:
                direction = np.array([float(node.get('x2', 0))-float(node.get('x1', 0)),
                                      float(node.get('y2', 0))-float(node.get('y1', 0))])
                direction = matrix @ direction
                if not np.isfinite(direction).all() or np.linalg.norm(direction) <= 0:
                    continue
                if symbol_strokes and np.linalg.norm(direction) <= max(vw, vh)*.25:
                    symbol_strokes -= 1
                    continue
                kind = stroke_kind(direction)
            except ValueError:
                continue
        if tag == 'rect':
            try:
                width, height = float(node.get('width', 0)), float(node.get('height', 0))
                if not np.isfinite([width,height]).all() or min(width,height) <= 0:
                    continue
                if symbol_strokes and 0 < min(width, height) <= narrow and max(width, height) > 3*min(width, height) and max(width, height) <= max(vw, vh)*.25:
                    symbol_strokes -= 1
                    continue
                x, y = float(node.get('x', 0)), float(node.get('y', 0))
                corners = np.array([[x, y], [x+width, y], [x+width, y+height], [x, y+height]]) @ matrix.T+translation
                edges = np.array([[width, 0], [0, height]]) @ matrix.T
                width, height = np.linalg.norm(edges, axis=1)
                if not np.isfinite(corners).all() or min(width, height) <= 0:
                    continue
                rectangle_key = (*corners[np.lexsort((corners[:, 1], corners[:, 0]))].ravel(), node.get('rx', '0'), node.get('ry', '0'))
                outline = node.get('fill', 'black') == 'none'
                # The neutral full-canvas backing is not another described rectangle.
                if ((node.get('fill', '').lower() in {'white', '#fff', '#ffffff'} or
                        ('rect' not in limits and 'square' not in limits) or
                        substantial_rectangles > limits.get('rect', 0))
                        and node.get('stroke', 'none') == 'none'
                        and np.all(corners.min(axis=0) <= np.array([vx, vy])+1e-6)
                        and np.all(corners.max(axis=0) >= np.array([vx+vw, vy+vh])-1e-6)):
                    continue
                if any(old[8:] == rectangle_key[8:] and rectangles[old] != outline
                       and max(abs(a-b) for a, b in zip(old[:8], rectangle_key[:8])) <= 1.01 for old in rectangles):
                    continue  # one field plus its independently layered border
                rectangles[rectangle_key] = outline
                if (node.get('stroke', 'none') == 'none' and node.get('fill', 'black') != 'none'
                        and not (foreground_count == 1 and 'rect' in limits and 'line' not in limits)
                        and 'url(' not in node.get('fill', '') and (area <= 0 or width*height < area*.5)
                        and 0 < min(width, height) <= narrow
                        and max(width, height) > 3*min(width, height)):
                    kind = 'line'
                elif abs(np.dot(*edges)) > width*height*FORM_TOLERANCE:
                    kind = 'polygon'
                elif (('square' in limits or 'rhombus' in limits) and min(width, height) > 0 and abs(width-height) < max(width, height)*FORM_TOLERANCE
                      and float(node.get('rx', 0)) == 0 and float(node.get('ry', 0)) == 0):
                    kind = 'square' if 'square' in limits else 'rhombus'
            except ValueError:
                continue
        if tag in {'polygon', 'polyline', 'path'}:
            paths = path_points(node)
            if not paths:
                # Curves and compound/unknown paths must not disappear from
                # the closed inventory and hide additional painted objects.
                inventory[tag] = inventory.get(tag, 0)+1
            for points, closed in paths:
                points = points @ matrix.T+translation
                if not np.isfinite(points).all():
                    continue
                vertices = _vertices(points, closed, epsilon=max(1e-7, float(np.ptp(points, axis=0).max())*1e-7))
                if not closed:
                    # A bent polyline cannot certify one straight object.
                    for a, b in zip(vertices, vertices[1:]):
                        kind = stroke_kind(b-a)
                        inventory[kind] = inventory.get(kind, 0)+1
                elif len(vertices) == 3:
                    inventory['triangle'] = inventory.get('triangle', 0)+1
                else:
                    if len(vertices) >= 4 and ('line' in limits or 'diagonal' in limits):
                        _, spans, _ = cv2.minAreaRect(vertices.astype(np.float32))
                        # A native clipped stroke is still a line when its
                        # width exceeds three pixels. Long, thin geometry is
                        # scale-independent evidence; the absolute threshold
                        # remains useful for short marks.
                        if (0 < min(spans) <= max(narrow,max(spans)*.1) and max(spans) > 3*min(spans)
                                and straight_strip(vertices)):
                            # A strip repainted with the surrounding field is
                            # negative geometry inside a hollow stroke.
                            if fields.get(node.get('fill', 'none'), 0) < cv2.contourArea(vertices.astype(np.float32))*4:
                                direction = np.linalg.svd(vertices-vertices.mean(axis=0), full_matrices=False)[2][0]
                                kind = stroke_kind(direction)
                                inventory[kind] = inventory.get(kind, 0)+1
                            continue
                    rectangle = False
                    if len(vertices) == 4:
                        edges = np.roll(vertices, -1, axis=0)-vertices
                        lengths = np.linalg.norm(edges, axis=1)
                        rectangle = bool(min(lengths) > 0 and np.max(abs(np.sum(edges*np.roll(edges, -1, axis=0), axis=1))
                            /np.maximum(1e-9, lengths*np.roll(lengths, -1))) < FORM_TOLERANCE)
                    if rectangle and 'square' in limits and max(lengths)-min(lengths) < max(lengths)*FORM_TOLERANCE:
                        kind = 'square'
                    elif (len(vertices) == 4 and 'rhombus' in limits and min(lengths) > 0
                          and max(lengths)-min(lengths) < max(lengths)*FORM_TOLERANCE
                          and cv2.isContourConvex(vertices.astype(np.float32))):
                        kind = 'rhombus'
                    else:
                        kind = 'rect' if rectangle and 'polygon' not in limits else 'polygon'
                    inventory[kind] = inventory.get(kind, 0)+1
            continue
        inventory[kind] = inventory.get(kind, 0)+1
    return inventory


def validate_object_limits(svg, limits, *, partial=False, complete=False, symbol_strokes=0, text_count=None):
    actual = logical_inventory(svg, limits, symbol_strokes)
    if text_count is not None:
        actual['text'] = text_count
    for kind, expected in limits.items():
        count = actual.get(kind, 0)
        if count > expected or (not partial and count != expected):
            raise ValueError(f'logical_object_count:{kind}:{expected}:{count}')
    if complete and sum(actual.values()) > sum(limits.values()):
        raise ValueError(f'logical_object_count:all:{sum(limits.values())}:{sum(actual.values())}')


def object_limit_excess(svg, limits, complete=False, symbol_strokes=0):
    actual = logical_inventory(svg, limits, symbol_strokes)
    excess = sum(max(0, actual.get(kind, 0)-count) for kind, count in limits.items())
    return max(excess, max(0, sum(actual.values())-sum(limits.values()))) if complete else excess


def simplification_proposals(svg):
    root = ET.fromstring(svg)
    for candidate, origin in consolidation_proposals(svg):
        yield candidate, origin
        # A convex hull can itself have a cheaper analytic representation.
        yield from _single_form_simplifications(candidate)
    yield from _single_form_simplifications(svg)


def _single_form_simplifications(svg):
    root = ET.fromstring(svg)
    for path, node in drawing_nodes(root):
        paths = path_points(node)
        if len(paths) != 1:
            continue
        points, closed = paths[0]
        vertices = _vertices(points, closed, .2)
        if len(vertices) < 2:
            continue
        tag, attrs = None, {}
        if not closed and len(vertices) == 2:
            tag, attrs = 'line', dict(zip(('x1', 'y1', 'x2', 'y2'), vertices.ravel()))
        elif closed and len(vertices) == 4:
            x, y = vertices.min(axis=0)
            X, Y = vertices.max(axis=0)
            corners = np.array([[x, y], [X, y], [X, Y], [x, Y]])
            if max(min(np.linalg.norm(corners-p, axis=1)) for p in vertices) < .01:
                tag, attrs = 'rect', dict(x=x, y=y, width=X-x, height=Y-y)
        elif closed and len(vertices) == 3:
            tag, attrs = 'polygon', dict(points=' '.join(f'{x:g},{y:g}' for x, y in vertices))
        if tag is None and closed and len(vertices) >= 8:
            (cx, cy), radius = cv2.minEnclosingCircle(points.astype(np.float32))
            if np.max(abs(np.linalg.norm(points-[cx, cy], axis=1)-radius)) <= .3:
                tag, attrs = 'circle', dict(cx=cx, cy=cy, r=radius)
            elif len(points) >= 5:
                (cx, cy), (aw, ah), angle = cv2.fitEllipse(points.astype(np.float32))
                if min(aw, ah) > 0:
                    theta = np.deg2rad(angle)
                    rotation = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
                    relative = (points-[cx, cy]) @ rotation / [aw/2, ah/2]
                    if np.max(abs(np.linalg.norm(relative, axis=1)-1))*min(aw, ah)/2 <= .3:
                        tag, attrs = 'ellipse', dict(cx=cx, cy=cy, rx=aw/2, ry=ah/2,
                            transform=node.get('transform', '')+f' rotate({angle:g} {cx:g} {cy:g})')
        if tag is None and len(vertices) < len(points):
            tag = 'polygon' if closed else 'polyline'
            attrs = dict(points=' '.join(f'{x:g},{y:g}' for x, y in vertices))
        if tag is None:
            continue
        candidate = copy.deepcopy(root)
        changed = candidate
        for index in path:
            changed = changed[index]
        changed.tag = '{http://www.w3.org/2000/svg}'+tag
        for key in ('d', 'points'):
            changed.attrib.pop(key, None)
        changed.attrib.update({key: str(value) for key, value in attrs.items()})
        result = ET.tostring(candidate, encoding='unicode')
        if representation_cost(result)['penalty'] < representation_cost(svg)['penalty']:
            yield result, 'simplify:'+tag


def consolidation_proposals(svg):
    """Fit one whole shape to same-paint fragments, always subject to rendering."""
    root = ET.fromstring(svg)
    geometry = {'id', 'x', 'y', 'width', 'height', 'cx', 'cy', 'r', 'x1', 'y1', 'x2', 'y2', 'd', 'points', 'rx', 'ry'}
    groups = {}
    for path, node in drawing_nodes(root):
        tag = node.tag.rsplit('}', 1)[-1]
        if tag not in {'line', 'polygon', 'polyline', 'path', 'rect', 'circle', 'ellipse'} or node.get('transform'):
            continue
        if node.get('id') and (f'url(#{node.get("id")})' in svg or f'href="#{node.get("id")}"' in svg):
            continue
        style = tuple(sorted((k, v) for k, v in node.attrib.items() if k not in geometry))
        points, closed = None, False
        try:
            if tag == 'line':
                points = np.array([[float(node.get('x1', 0)), float(node.get('y1', 0))],
                                   [float(node.get('x2', 0)), float(node.get('y2', 0))]])
            elif tag == 'rect' and node.get('fill', 'black') != 'none':
                x, y, w, h = (float(node.get(k, 0)) for k in ('x', 'y', 'width', 'height'))
                points, closed = np.array([[x, y], [x+w, y], [x+w, y+h], [x, y+h]]), True
            elif tag in {'circle', 'ellipse'}:
                cx, cy = float(node.get('cx', 0)), float(node.get('cy', 0))
                rx, ry = (float(node.get('r', 0)),)*2 if tag == 'circle' else (float(node.get('rx', 0)), float(node.get('ry', 0)))
                angles = np.linspace(0, 2*np.pi, 32, endpoint=False)
                points, closed = np.c_[cx+rx*np.cos(angles), cy+ry*np.sin(angles)], True
            else:
                paths = path_points(node)
                if len(paths) == 1:
                    points, closed = paths[0]
        except ValueError:
            continue
        if points is not None and np.isfinite(points).all():
            groups.setdefault((path[:-1], closed, style), []).append((path, node, points))
    for (parent_path, closed, _), parts in groups.items():
        if len(parts) < 3:
            continue
        points = np.concatenate([p for _, _, p in parts])
        attrs, tag = {}, None
        if closed:
            hull = cv2.convexHull(points.astype(np.float32))[:, 0]
            if len(hull) >= 3:
                tag, attrs = 'polygon', dict(points=' '.join(f'{x:g},{y:g}' for x, y in hull))
        else:
            center = points.mean(axis=0)
            axis = np.linalg.svd(points-center, full_matrices=False)[2][0]
            distance = abs((points-center) @ np.array([-axis[1], axis[0]]))
            try:
                width = float(parts[0][1].get('stroke-width', '1'))
            except ValueError:
                width = 1.
            if max(distance) <= max(2., width*2):
                along = (points-center) @ axis
                a, b = center+min(along)*axis, center+max(along)*axis
                tag, attrs = 'line', dict(zip(('x1', 'y1', 'x2', 'y2'), np.r_[a, b]))
        if tag is None:
            continue
        candidate = copy.deepcopy(root)
        parent = candidate
        for index in parent_path:
            parent = parent[index]
        replacement = copy.deepcopy(parts[0][1])
        replacement.tag = '{http://www.w3.org/2000/svg}'+tag
        for key in geometry-{'id'}:
            replacement.attrib.pop(key, None)
        replacement.attrib.update({key: str(value) for key, value in attrs.items()})
        for path, _, _ in sorted(parts, key=lambda p: p[0], reverse=True):
            del parent[path[-1]]
        parent.insert(min(p[0][-1] for p in parts), replacement)
        result = ET.tostring(candidate, encoding='unicode')
        if representation_cost(result)['penalty'] < representation_cost(svg)['penalty']:
            yield result, 'simplify:consolidate_'+tag
