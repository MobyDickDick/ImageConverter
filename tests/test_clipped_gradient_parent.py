"""Canvas clipping may hide a parent arc, never evidence for a child or rim."""
from copy import deepcopy
from xml.etree import ElementTree as ET

import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterMixedGradientScene as mixed
from tests.test_residual_scene_search import fit
from tests.test_structure_search_operators import assert_accepted
from tools.evaluate_mixed_overlap import make_cases, make_variation_cases
from tools.run_plan_b_variations import render


@pytest.mark.parametrize('index', range(12))
def test_clipped_edges_and_corners_retain_native_objects_and_depth(index):
    case = make_cases(618293, groups=2, rounded=True, outlined=True, clipped_parent=True)[index]
    image, result = fit(case)
    assert_accepted(case, image, result)
    assert sum(a['outcome'] == 'accepted' for a in result['scene_attempts']) == 1


@pytest.mark.parametrize('name', ['probe_08', 'probe_12', 'probe_13'])
def test_previously_rejected_coupled_variants_keep_full_object_checks(name):
    case = next(c for c in make_variation_cases(853197, groups=2, rounded=True, outlined=True)
                if c['case_id'] == name)
    image, result = fit(case)
    assert_accepted(case, image, result)


@pytest.mark.parametrize('outlined', [False, True])
def test_clipped_parent_also_works_with_a_connected_group(outlined):
    case = make_cases(618293, rounded=True, outlined=outlined, clipped_parent=True)[5]
    image, result = fit(case)
    assert_accepted(case, image, result)


@pytest.mark.parametrize('damage', ['missing_child', 'extra_child', 'wrong_axis',
                                  'dark_parent_rim', 'missing_parent_rim', 'texture'])
def test_clipping_does_not_excuse_other_description_or_raster_failures(damage):
    case = deepcopy(make_cases(618293, groups=2, rounded=True, outlined=True,
                               clipped_parent=True)[4])
    root = ET.fromstring(case['svg'])
    if damage == 'missing_child':
        root.remove(root[-1])
    elif damage == 'extra_child':
        ET.SubElement(root, 'rect', x='100', y='230', width='15', height='15', fill='#123456')
    elif damage == 'wrong_axis':
        case['description'] = case['description'].replace('horizontalen', 'vertikalen')
    elif damage == 'dark_parent_rim':
        root[2].set('stroke', '#202020')
    elif damage == 'missing_parent_rim':
        root[2].set('stroke', 'none')
    else:
        # Erase a substantial part of a small child's fill. Object-local
        # quality, rather than the large parent's area, must decide this.
        ET.SubElement(root, 'rect', x='140', y='150', width='15', height='15', fill='white')
    case['svg'] = ET.tostring(root, encoding='unicode')
    assert fit(case)[1] is None


@pytest.mark.parametrize('x,accepted', [(3., True), (-2., False)])
def test_a_clipped_child_is_still_rejected_even_with_an_exact_raster_fit(x, accepted):
    from src.iCCModules.imageCompositeConverterSearchScheduler import drain
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy, image_search

    # The child is contained by the cropped parent even when it crosses the
    # canvas. A positive exact-fit control distinguishes the two contracts.
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200">'
           '<defs><linearGradient id="p"><stop offset="0" stop-color="#bbd9eb"/>'
           '<stop offset="1" stop-color="#6198b3"/></linearGradient></defs>'
           '<rect width="200" height="200" fill="white"/>'
           '<circle cx="50" cy="100" r="90" fill="url(#p)"/>'
           f'<rect x="{x}" y="80" width="25" height="30" fill="#284d79"/></svg>')
    objects = [dict(kind='circle', geometry=np.array([-40., 10., 180., 180., 0.]),
                    colors=np.array([235., 217., 187., 179., 152., 97., 255., 255., 255.])),
               dict(kind='rectangle', geometry=np.array([x, 80., 25., 30., 0.]),
                    colors=np.array([121., 77., 40., 121., 77., 40., 255., 255., 255.]))]
    contract = mixed.scene_contract('Ein gefüllter Kreis und ein gefülltes Rechteck. '
        'Der Kreis hat einen horizontalen Farbverlauf. '
        'Die Rechtecke liegen innerhalb des Kreises. Keine Beschriftung.')
    with image_search(ImageSearch(SearchPolicy(seconds=5, max_seconds=5))):
        result = drain(mixed._fit_instances_steps(200, 200, pixels=render(svg, 200, 200),
            contract=contract, objects=objects, render_fn=render,
            error_fn=lambda a, b: float(abs(a.astype(float)-b).mean())))
    assert (result is not None) == accepted


@pytest.mark.parametrize('cx,cy,radius', [(100., 100., 130.), (-10., 100., 80.),
                                      (100., 100., 500.)])
def test_unobservable_or_less_than_half_parent_arcs_are_not_invented(cx, cy, radius):
    import cv2

    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200">'
           '<rect width="200" height="200" fill="white"/>'
           f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="#6198b3"/></svg>')
    pixels = render(svg, 200, 200)
    mask = (np.max(255-pixels.astype(float), axis=2) > 25).astype('uint8')
    contour = max(cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0],
                  key=cv2.contourArea)
    assert mixed._parent_circle(contour, mask.shape) is None


def test_a_clipped_ellipse_cannot_supply_circle_curvature():
    import cv2

    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="360" height="360">'
           '<rect width="360" height="360" fill="white"/>'
           '<ellipse cx="210" cy="180" rx="195" ry="165" fill="#6198b3"/></svg>')
    pixels = render(svg, 360, 360)
    mask = (np.max(255-pixels.astype(float), axis=2) > 25).astype('uint8')
    contour = max(cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0],
                  key=cv2.contourArea)
    assert mixed._parent_circle(contour, mask.shape) is None


def test_budget_exhaustion_does_not_start_a_clipped_parent_proposal(monkeypatch):
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy

    session = ImageSearch(SearchPolicy(seconds=1, max_seconds=1))
    session.spent = 2
    monkeypatch.setattr(mixed, '_parent_circle', lambda *a: pytest.fail('Budget exhausted'))
    case = make_cases(618293, groups=2, clipped_parent=True)[0]
    assert fit(case, session)[1] is None
