"""Check described native arrow heads in their displayed coordinate system."""
from __future__ import annotations

import math
import re


def _compose(a, b):
    return (a[0]*b[0]+a[2]*b[1], a[1]*b[0]+a[3]*b[1],
            a[0]*b[2]+a[2]*b[3], a[1]*b[2]+a[3]*b[3],
            a[0]*b[4]+a[2]*b[5]+a[4], a[1]*b[4]+a[3]*b[5]+a[5])


def _transform(value):
    matrix = (1., 0., 0., 1., 0., 0.)
    cursor = 0
    for match in re.finditer(r'(matrix|translate|scale|rotate)\s*\(([^)]*)\)', value):
        if value[cursor:match.start()].strip(' \t\r\n,'):
            raise ValueError('unsupported transform')
        v = [float(x) for x in re.split(r'[\s,]+', match[2].strip())]
        if not all(math.isfinite(x) for x in v):
            raise ValueError('nonfinite transform')
        kind = match[1]
        if kind == 'matrix' and len(v) == 6:
            local = tuple(v)
        elif kind == 'translate' and len(v) in (1, 2):
            local = (1, 0, 0, 1, v[0], v[1] if len(v) == 2 else 0)
        elif kind == 'scale' and len(v) in (1, 2):
            local = (v[0], 0, 0, v[1] if len(v) == 2 else v[0], 0, 0)
        elif kind == 'rotate' and len(v) in (1, 3):
            c, s = math.cos(math.radians(v[0])), math.sin(math.radians(v[0]))
            x, y = v[1:] if len(v) == 3 else (0, 0)
            local = (c, s, -s, c, x-c*x+s*y, y-s*x-c*y)
        else:
            raise ValueError('invalid transform')
        matrix = _compose(matrix, local)
        cursor = match.end()
    if value[cursor:].strip(' \t\r\n,'):
        raise ValueError('unsupported transform')
    return matrix


def validate_arrow_heads(root, expected):
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import DescriptionRejected

    heads = []
    def visit(node, parent=(1., 0., 0., 1., 0., 0.), fill='black'):
        kind = node.tag.rsplit('}', 1)[-1]
        if kind in {'defs', 'clipPath', 'mask', 'symbol', 'pattern', 'marker'}:
            return
        matrix = _compose(parent, _transform(node.get('transform', '')))
        fill = node.get('fill', fill)
        if kind == 'polygon':
            values = [float(v) for v in re.split(r'[\s,]+', node.get('points', '').strip())]
            if len(values) != 6 or not all(math.isfinite(v) for v in values):
                raise ValueError('invalid triangle')
            a, b, c, d, e, f = matrix
            points = [(a*x+c*y+e, b*x+d*y+f) for x, y in zip(values[::2], values[1::2])]
            # A vertical arrow has a broad, nearly horizontal base and a
            # centered apex. Counting three arbitrary points cannot prove it.
            candidates = []
            for i in range(3):
                tip, left, right = points[i], points[(i+1)%3], points[(i+2)%3]
                width = abs(left[0]-right[0])
                base_y = (left[1]+right[1])/2
                height = abs(tip[1]-base_y)
                if (width > 1e-6 and height >= width*.3
                        and abs(left[1]-right[1]) <= height*.15
                        and abs(tip[0]-(left[0]+right[0])/2) <= width*.25):
                    candidates.append((sum(p[0] for p in points)/3,
                                       'down' if tip[1] > base_y else 'up'))
            if len(candidates) != 1:
                raise ValueError('deformed triangle')
            heads.extend((x, direction, fill) for x, direction in candidates)
        for child in node:
            visit(child, matrix, fill)
    try:
        visit(root)
    except (ValueError, OverflowError) as exc:
        raise DescriptionRejected('invalid_described_arrow_head') from exc
    heads.sort()
    if len(heads) != 2 or heads[1][0]-heads[0][0] <= 1e-6:
        raise DescriptionRejected('missing_separate_arrow_heads')
    for claim in expected:
        index = 0 if claim['side'] == 'left' else 1
        if heads[index][1] != claim['direction']:
            raise DescriptionRejected('wrong_described_arrow_direction:'+claim['side'])
        if claim.get('color'):
            from PIL import ImageColor
            try:
                r, g, b = ImageColor.getrgb(heads[index][2])
                matches = (r > g+30 and r > b+30 if claim['color'] == 'red'
                           else b > r+30 and b > g+15)
            except (ValueError, TypeError):
                matches = False
            if not matches:
                raise DescriptionRejected('wrong_described_arrow_color:'+claim['side'])
