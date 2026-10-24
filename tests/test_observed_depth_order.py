"""Image-derived depth proposals must retain the native and raster contracts."""
from copy import deepcopy
from xml.etree import ElementTree as ET

import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterMixedGradientScene as mixed
from tests.test_residual_scene_search import fit
from tests.test_structure_search_operators import assert_accepted
from tools.evaluate_overlap_composition import make_cases


INSUFFICIENT_CORNERS = {(5, True, True, 0), (6, True, True, 0), (8, True, False, 1)}


@pytest.mark.parametrize('children,rounded,outlined,index', [
    (n, rounded, outlined, index) for n in (5, 6, 8)
    for rounded, outlined in ((False, False), (True, False), (False, True), (True, True))
    for index in (0, 1, 3) if (n, rounded, outlined, index) not in INSUFFICIENT_CORNERS])
def test_observed_depth_supports_larger_inventories(children, rounded, outlined, index):
    case = make_cases(seed=527183, children=children, rounded=rounded, outlined=outlined)[index]
    image, result = fit(case)
    assert_accepted(case, image, result)
    assert result['scene_hypotheses'] <= 4


@pytest.mark.parametrize('children,rounded,outlined,index', sorted(INSUFFICIENT_CORNERS))
def test_crowded_rounding_without_two_radius_measurements_remains_rejected(children, rounded, outlined, index):
    case = make_cases(seed=527183, children=children, rounded=rounded, outlined=outlined)[index]
    image, result = fit(case)
    assert mixed.detect_instances(image, mixed.scene_contract(case['description'])) is None
    assert result is None


@pytest.mark.parametrize('index', [0, 3, 10])
def test_occlusion_blends_do_not_replace_observed_native_sides(index):
    case = make_cases(seed=962431, children=8)[index]
    image, result = fit(case)
    assert_accepted(case, image, result)


@pytest.mark.parametrize('damage', ['missing', 'same_color', 'wrong_count', 'hidden_side', 'outside', 'texture'])
def test_more_layers_cannot_erase_missing_or_contradictory_evidence(damage):
    case = deepcopy(make_cases(children=6)[0])
    root = ET.fromstring(case['svg'])
    if damage == 'missing':
        root.remove(root[-1])
    elif damage == 'same_color':
        root[-1].set('fill', root[-2].get('fill'))
    elif damage == 'wrong_count':
        case['description'] = case['description'].replace('sechs', 'sieben')
    elif damage == 'hidden_side':
        root[-1].set('x', root[-2].get('x'))
        root[-1].set('width', root[-2].get('width'))
    elif damage == 'outside':
        root[-1].set('x', '282')
    else:
        ET.SubElement(root, 'rect', x='140', y='140', width='12', height='12', fill='white')
    case['svg'] = ET.tostring(root, encoding='unicode')
    assert fit(case)[1] is None


def test_inconsistent_local_depth_cycle_has_no_ordering_proposal():
    image = np.full((90, 90, 3), 255, dtype='uint8')
    paints = [np.array(c, dtype=float) for c in [(30, 60, 90), (120, 30, 60), (60, 120, 30)]]
    boxes = [[10, 10, 60, 30, 0], [45, 15, 30, 60, 0], [15, 35, 50, 30, 0]]
    children = [dict(kind='rectangle', geometry=np.array(box, dtype=float), colors=np.tile(paint, 3))
                for box, paint in zip(boxes, paints)]
    # Pair-exclusive patches demand A before B, B before C, C before A.
    # Such local paint cannot represent one global painter order.
    image[20:30, 50:65] = paints[1]
    image[45:55, 50:60] = paints[2]
    image[37:38, 20:40] = paints[0]
    assert mixed.observed_painter_order(image, [None, *children]) is None
