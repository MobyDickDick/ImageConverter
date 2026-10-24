"""Same paint is a grouping hypothesis, never proof of a single instance."""
from copy import deepcopy
from xml.etree import ElementTree as ET

import pytest

from tests.test_residual_scene_search import fit
from tests.test_structure_search_operators import assert_accepted
from tools.evaluate_mixed_overlap import make_cases


@pytest.mark.parametrize('children', [5, 6, 8])
@pytest.mark.parametrize('rounded,outlined', [(False, False), (True, False), (False, True), (True, True)])
@pytest.mark.parametrize('index', [0, 1])
def test_repeated_fill_instances_require_separate_observed_bounds(children, rounded, outlined, index):
    case = make_cases(527183, children=children, repeat_fill=True,
                      rounded=rounded, outlined=outlined)[index]
    image, result = fit(case)
    assert_accepted(case, image, result)
    accepted = [a for a in result['scene_attempts'] if a['outcome'] == 'accepted']
    assert len(accepted) == 1
    assert accepted[0]['operator'] == 'split'
    assert accepted[0]['painter_order'] == 'observed_depth'


@pytest.mark.parametrize('outlined', [False, True])
def test_repeated_rectangles_and_circles_share_the_same_split_search(outlined):
    case = make_cases(527183, children=6, repeat_fill=True, rounded=True, outlined=outlined)[0]
    root = ET.fromstring(case['svg'])
    root[-1].set('fill', root[-5].get('fill'))
    case['svg'] = ET.tostring(root, encoding='unicode')
    image, result = fit(case)
    assert_accepted(case, image, result)


@pytest.mark.parametrize('damage', ['missing', 'extra_same_paint', 'wrong_count', 'hidden_arc', 'texture'])
def test_splitting_same_paint_does_not_waive_native_or_raster_evidence(damage):
    case = deepcopy(make_cases(527183, children=6, repeat_fill=True, rounded=True, outlined=True)[0])
    root = ET.fromstring(case['svg'])
    if damage == 'missing':
        root.remove(root[-2])
    elif damage == 'extra_same_paint':
        extra = ET.SubElement(root, 'circle', cx='240', cy='105', r='12')
        for key in ('fill', 'stroke', 'stroke-width'):
            extra.set(key, root[3].get(key))
    elif damage == 'wrong_count':
        case['description'] = case['description'].replace('4 gefüllte Kreise', '3 gefüllte Kreise')
    elif damage == 'hidden_arc':
        circle, rectangle = root[3:5]
        cx, cy, radius = (float(circle.get(k)) for k in ('cx', 'cy', 'r'))
        rectangle.attrib.update(x=str(cx-4), y=str(cy-radius-5),
                                width=str(radius+14), height=str(2*radius+10))
    else:
        ET.SubElement(root, 'rect', x='105', y='100', width='15', height='12', fill='white')
    case['svg'] = ET.tostring(root, encoding='unicode')
    assert fit(case)[1] is None


def test_one_occluded_circle_keeps_its_union_of_visible_islands():
    case = make_cases()[0]
    root = ET.fromstring(case['svg'])
    circle, rectangle = root[-2:]
    cx, cy, radius = (float(circle.get(k)) for k in ('cx', 'cy', 'r'))
    box = [cx-5, cy-radius-10, 10, 2*radius+20]
    rectangle.attrib.update(zip(('x', 'y', 'width', 'height'), map(str, box)))
    case['expected_objects'][-1]['bbox'] = box
    case['svg'] = ET.tostring(root, encoding='unicode')
    image, result = fit(case)
    assert_accepted(case, image, result)
    assert result['scene_attempts'][0]['operator'] == 'segmentation'
