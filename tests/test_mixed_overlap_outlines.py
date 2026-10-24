"""Occluded circle rims need distinct observed radii and unchanged scene gates."""
from copy import deepcopy
from xml.etree import ElementTree as ET

import pytest

from src.iCCModules import imageCompositeConverterMixedGradientScene as mixed
from tests.test_residual_scene_search import fit
from tests.test_structure_search_operators import assert_accepted
from tools.evaluate_mixed_overlap import make_cases


@pytest.mark.parametrize('rounded', [False, True])
@pytest.mark.parametrize('index', range(12))
def test_observed_circle_and_rectangle_rims_earn_native_acceptance(index, rounded):
    case = make_cases(731921, rounded=rounded, outlined=True)[index]
    image, result = fit(case)
    assert_accepted(case, image, result)
    assert result['scene_attempts'][0]['painter_order'] == 'observed_depth'
    assert sum(a['outcome'] == 'accepted' for a in result['scene_attempts']) == 1
    assert sum(a['operator'] == 'edit' for a in result['scene_attempts']) <= 96


@pytest.mark.parametrize('damage', ['missing_rim', 'dark_rim', 'missing_parent_rim',
    'ellipse', 'square', 'extra', 'hidden_arc', 'texture', 'disjoint'])
def test_circle_rims_cannot_excuse_missing_or_contradictory_evidence(damage):
    case = deepcopy(make_cases(731921, rounded=True, outlined=True)[0])
    root = ET.fromstring(case['svg'])
    parent, circle, rectangle = root[-3:]
    cx, cy, radius = (float(circle.get(k)) for k in ('cx', 'cy', 'r'))
    if damage == 'missing_rim':
        circle.set('stroke', 'none')
    elif damage == 'dark_rim':
        circle.set('stroke', '#343434')
    elif damage == 'missing_parent_rim':
        parent.set('stroke', 'none')
    elif damage in ('ellipse', 'square'):
        root.remove(circle)
        replacement = ET.Element('ellipse', cx=str(cx), cy=str(cy), rx=str(radius), ry=str(radius*.65)) if damage == 'ellipse' else ET.Element(
            'rect', x=str(cx-radius), y=str(cy-radius), width=str(2*radius), height=str(2*radius))
        for key in ('fill', 'stroke', 'stroke-width'):
            replacement.set(key, circle.get(key))
        root.insert(len(root)-1, replacement)
    elif damage == 'extra':
        ET.SubElement(root, 'circle', cx='160', cy='68', r='12', fill='#765232')
    elif damage == 'hidden_arc':
        rectangle.attrib.update(x=str(cx-4), y=str(cy-radius-5),
            width=str(radius+14), height=str(2*radius+10))
    elif damage == 'texture':
        ET.SubElement(root, 'rect', x=str(cx-13), y=str(cy-13), width='15', height='12', fill='white')
    else:
        rectangle.set('x', '134')
    case['svg'] = ET.tostring(root, encoding='unicode')
    assert fit(case)[1] is None


def test_contract_still_requires_every_additional_assertion():
    text = make_cases(outlined=True)[0]['description']
    assert mixed.scene_contract(text) is not None
    for claim in (' Der innere Kreis ist nicht gefüllt.', ' Mit Text.',
                  ' Die Kreise haben gerundete Ecken.', ' Die Formen sind getrennt.'):
        assert mixed.scene_contract(text+claim) is None
