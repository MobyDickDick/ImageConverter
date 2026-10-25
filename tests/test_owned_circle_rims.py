"""A circle's measured fill owns its rim; neighbouring equal paint does not."""
from copy import deepcopy
from xml.etree import ElementTree as ET

import pytest

from tests.test_residual_scene_search import fit
from tests.test_structure_search_operators import assert_accepted
from tools.evaluate_mixed_overlap import make_cases


@pytest.mark.parametrize('rounded', [False, True])
@pytest.mark.parametrize('index', range(12))
def test_independent_equal_paint_circle_rectangle_scenes(rounded, index):
    case = make_cases(529713, children=2, rounded=rounded, outlined=True, same_fill=True)[index]
    image, result = fit(case)
    if index == 6 and not rounded:
        # This valid scene has no pixel centers in the square rectangle's
        # conservative rim-depth band. Preserve the required five observed
        # samples; the new outer-circle proposal cannot supply depth evidence.
        assert result is None
        return
    assert_accepted(case, image, result)


@pytest.mark.parametrize('index', [2, 3])
@pytest.mark.parametrize('damage', ['ellipse', 'square', 'missing_rim', 'dark_rim',
                                   'texture', 'extra_same_paint', 'missing', 'wrong_count'])
def test_owned_fill_does_not_excuse_wrong_geometry_or_foreign_objects(index, damage):
    case = deepcopy(make_cases(731921, children=2, rounded=True, outlined=True, same_fill=True)[index])
    root = ET.fromstring(case['svg'])
    circle = root[-1]
    cx, cy, radius = (float(circle.get(key)) for key in ('cx', 'cy', 'r'))
    if damage in {'ellipse', 'square'}:
        root.remove(circle)
        replacement = (ET.Element('ellipse', cx=str(cx), cy=str(cy), rx=str(radius), ry=str(radius*.65))
                       if damage == 'ellipse' else ET.Element('rect', x=str(cx-radius), y=str(cy-radius),
                                                              width=str(2*radius), height=str(2*radius)))
        for key in ('fill', 'stroke', 'stroke-width'):
            replacement.set(key, circle.get(key))
        root.append(replacement)
    elif damage in {'missing_rim', 'dark_rim'}:
        circle.set('stroke', 'none' if damage == 'missing_rim' else '#343434')
    elif damage == 'texture':
        ET.SubElement(root, 'rect', x=str(cx-10), y=str(cy-10), width='12', height='10', fill='white')
    elif damage == 'extra_same_paint':
        ET.SubElement(root, 'circle', cx='162', cy='85', r='11', fill=circle.get('fill'),
                      stroke=circle.get('stroke'), **{'stroke-width': circle.get('stroke-width')})
    elif damage == 'missing':
        root.remove(circle)
    else:
        case['description'] = case['description'].replace('2 gefüllte Kreise', '3 gefüllte Kreise')
    case['svg'] = ET.tostring(root, encoding='unicode')
    assert fit(case)[1] is None
