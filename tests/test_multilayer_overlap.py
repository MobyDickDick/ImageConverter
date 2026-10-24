"""More than two observed children share the same bounded structure search."""
from copy import deepcopy
from xml.etree import ElementTree as ET

import pytest

from src.iCCModules import imageCompositeConverterMixedGradientScene as mixed
from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy
from tests.test_residual_scene_search import fit
from tests.test_structure_search_operators import assert_accepted
from tools.evaluate_layered_scene import check_objects
from tools.evaluate_overlap_composition import make_cases


@pytest.mark.parametrize('children', [3, 4])
@pytest.mark.parametrize('rounded,outlined', [(False, False), (True, False), (False, True), (True, True)])
@pytest.mark.parametrize('index', range(12))
def test_more_layers_preserve_native_objects_and_painter_order(children, rounded, outlined, index):
    case = make_cases(children=children, rounded=rounded, outlined=outlined)[index]
    session = ImageSearch(SearchPolicy(seconds=5, max_seconds=5))
    image, result = fit(case, session)
    assert_accepted(case, image, result)


@pytest.mark.parametrize('damage', ['missing', 'same_color', 'wrong_count', 'hidden_side', 'outside', 'texture'])
def test_multilayer_cannot_accept_missing_or_unobserved_geometry(damage):
    case = deepcopy(make_cases(children=3)[0])
    root = ET.fromstring(case['svg'])
    if damage == 'missing':
        root.remove(root[-1])
    elif damage == 'same_color':
        root[-1].set('fill', root[-2].get('fill'))
    elif damage == 'wrong_count':
        case['description'] = case['description'].replace('drei', 'vier')
    elif damage == 'hidden_side':
        root[-1].set('x', root[-2].get('x'))
        root[-1].set('width', root[-2].get('width'))
    elif damage == 'outside':
        root[-1].set('x', '172')
    else:
        ET.SubElement(root, 'rect', x='100', y='100', width='12', height='12', fill='white')
    case['svg'] = ET.tostring(root, encoding='unicode')
    assert fit(case)[1] is None


def test_independent_oracle_catches_later_layer_swap():
    case = make_cases(children=3)[1]
    root = ET.fromstring(case['svg'])
    assert check_objects(case['svg'], case['expected_objects'])['passed']
    moved = root[-2]
    root.remove(moved)
    root.append(moved)
    assert not check_objects(ET.tostring(root, encoding='unicode'), case['expected_objects'])['passed']


def test_more_than_four_overlap_children_remain_unsupported():
    text = make_cases(children=4)[0]['description'].replace('vier', 'fünf')
    assert mixed.scene_contract(text) is None
