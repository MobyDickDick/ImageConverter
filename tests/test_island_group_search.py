"""Mixed instance/island hypotheses must earn native and original-raster gates."""
from copy import deepcopy
from xml.etree import ElementTree as ET

import pytest
import numpy as np

from src.iCCModules import imageCompositeConverterMixedGradientScene as mixed
from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy, image_search
from tests.test_residual_scene_search import fit
from tests.test_structure_search_operators import assert_accepted
from tools.evaluate_island_groups import make_cases
from tools.run_plan_b_variations import render


@pytest.mark.parametrize('children', [3, 4])
@pytest.mark.parametrize('rounded,outlined', [(False, False), (True, False), (False, True), (True, True)])
@pytest.mark.parametrize('index', [0, 2])
def test_same_paint_instances_can_each_have_multiple_visible_islands(children, rounded, outlined, index):
    case = make_cases(children=children, rounded=rounded, outlined=outlined)[index]
    image, result = fit(case)
    assert_accepted(case, image, result)
    accepted = [a for a in result['scene_attempts'] if a['outcome'] == 'accepted']
    assert len(accepted) == 1
    assert accepted[0]['operator'] == 'group_islands'
    assert accepted[0]['painter_order'] == 'observed_depth'


@pytest.mark.parametrize('damage', ['missing', 'extra', 'wrong_count', 'hidden_arc', 'texture',
                                    'missing_rim', 'dark_rim', 'square'])
def test_grouping_cannot_invent_occluded_geometry_or_drop_raster_evidence(damage):
    case = deepcopy(make_cases(rounded=True, outlined=True)[0])
    root = ET.fromstring(case['svg'])
    if damage == 'missing':
        root.remove(root[-2])
    elif damage == 'extra':
        ET.SubElement(root, 'circle', cx='160', cy='100', r='12', fill=root[3].get('fill'))
    elif damage == 'wrong_count':
        case['description'] = case['description'].replace('3 gefüllte Kreise', '4 gefüllte Kreise')
    elif damage == 'hidden_arc':
        # Only small caps remain; the observed arc cannot determine a circle.
        bridge = root[-1]
        bridge.set('y', '134')
        bridge.set('height', '52')
    elif damage == 'texture':
        ET.SubElement(root, 'rect', x='100', y='140', width='12', height='10', fill='white')
    elif damage in ('missing_rim', 'dark_rim'):
        root[3].set('stroke', 'none' if damage == 'missing_rim' else '#222222')
    else:
        root[-1].set('rx', '0')
    case['svg'] = ET.tostring(root, encoding='unicode')
    assert fit(case)[1] is None


@pytest.mark.parametrize('seed,children,index', [(418267, 3, 4), (392841, 4, 11)])
def test_native_rounding_is_measured_at_the_centerline_of_a_visible_rim(seed, children, index):
    case = make_cases(seed, children=children, rounded=True, outlined=True)[index]
    image, result = fit(case)
    assert_accepted(case, image, result)


def test_four_exposed_side_samples_do_not_replace_the_required_five():
    # The narrow rounded bridge exposes only four pure-fill top samples.
    # Preserve this conservative boundary even though the scene is valid.
    assert fit(make_cases(418267, rounded=True, outlined=True)[6])[1] is None


@pytest.mark.parametrize('rectangles', [1, 2])
def test_island_groups_support_same_paint_across_native_shape_types(rectangles):
    case = make_cases()[0]
    root = ET.fromstring(case['svg'])
    for element in list(root)[3:3+rectangles]:
        cx, cy, r = (float(element.get(k)) for k in ('cx', 'cy', 'r'))
        element.tag = '{http://www.w3.org/2000/svg}rect'
        for key in ('cx', 'cy', 'r'):
            del element.attrib[key]
        element.attrib.update(x=str(cx-r), y=str(cy-r), width=str(2*r), height=str(2*r))
    for obj in case['expected_objects'][1:1+rectangles]:
        obj['kind'] = 'rectangle'
    case['description'] = case['description'].replace('3 gefüllte Kreise und ein gefülltes Rechteck',
        f'{3-rectangles} gefüllte Kreise und {1+rectangles} gefüllte Rechtecke')
    case['svg'] = ET.tostring(root, encoding='unicode')
    image, result = fit(case)
    assert_accepted(case, image, result)


@pytest.mark.parametrize('limit', [12, 96])
def test_grouping_yields_exact_covers_and_respects_the_shared_state_limit(limit):
    case = make_cases(children=4)[0]
    pixels = render(case['svg'], case['width'], case['height'])
    contract = mixed.scene_contract(case['description'])
    context = mixed._gradient_context(pixels, contract, 25)
    paints = mixed._paint_components(pixels, context[3])
    stats, complete = {}, 0
    for groups in mixed._island_partitions(paints, 4, max_states=limit, stats=stats):
        if groups is not None:
            complete += 1
            assert len(groups) == 4
            for color, labels, parts in paints:
                masks = [mask for paint, mask in groups if (paint == color).all()]
                coverage = sum(mask.astype(int) for mask in masks)
                assert (coverage == (labels > 0)).all()
    if limit == 96:
        assert complete > 0
    assert stats['states'] <= limit
    assert stats['state_limit_reached']


def test_an_expired_budget_never_starts_grouping_detection(monkeypatch):
    session = ImageSearch(SearchPolicy(seconds=1, max_seconds=1))
    session.spent = 2
    monkeypatch.setattr(mixed, '_gradient_context', lambda *a: pytest.fail('Budget already spent'))
    with image_search(session):
        assert list(mixed.grouped_overlap_instances(None, {}, max_states=96, stats={})) == []


def test_grouping_reports_states_without_exceeding_the_combined_edit_limit(monkeypatch):
    events = []
    monkeypatch.setattr(mixed, 'progress', lambda *a, **kw: events.append(kw))
    case = make_cases(rounded=True, outlined=True)[0]
    image, result = fit(case)
    assert_accepted(case, image, result)
    final = next(e for e in events if e.get('event') == 'structure_search_finished')
    assert final['outcome'] == 'accepted'
    assert 1 < final['states'] <= 96
    assert 1 < final['grouping_states'] <= final['states']


def test_too_many_observed_islands_cannot_expand_the_partition_agenda():
    paints = [(np.array([30, 60, 90]), np.arange(17).reshape(1, 17), list(range(1, 17))),
              (np.array([90, 60, 30]), np.ones((1, 17), dtype=int), [1])]
    stats = {}
    assert list(mixed._island_partitions(paints, 3, max_states=96, stats=stats)) == []
    assert stats['states'] == 0
    assert stats['candidate_limit_reached']


def test_grouping_rejections_remain_bound_to_the_image_and_contract(monkeypatch):
    calls, events = [], []

    def reject(*a, **kw):
        calls.append(1)
        yield None
        return None

    monkeypatch.setattr(mixed, '_fit_instances_steps', reject)
    monkeypatch.setattr(mixed, 'progress', lambda *a, **kw: events.append(kw))
    session = ImageSearch(SearchPolicy(seconds=60, max_seconds=60))
    case = make_cases()[0]
    assert fit(case, session)[1] is None
    first = len(calls)
    assert first > 0
    assert fit(case, session)[1] is None
    assert len(calls) == first
    assert any(e.get('outcome') == 'native_boundaries_rejected' for e in events)
    assert any(e.get('operator') == 'group_islands' and e.get('outcome') == 'previously_rejected'
               for e in events)
