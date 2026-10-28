"""Disconnected overlap groups share native fitting and a complete topology contract."""
from copy import deepcopy
from xml.etree import ElementTree as ET

import pytest

from src.iCCModules import imageCompositeConverterMixedGradientScene as mixed
from tests.test_residual_scene_search import fit
from tests.test_structure_search_operators import assert_accepted
from tools.evaluate_mixed_overlap import make_cases


@pytest.mark.parametrize('groups', [2, 3, 4])
@pytest.mark.parametrize('rounded,outlined', [(False, False), (True, True)])
@pytest.mark.parametrize('index', [0, 1, 3])
def test_every_disconnected_group_retains_objects_and_observed_depth(groups, rounded, outlined, index):
    case = make_cases(731429, groups=groups, rounded=rounded, outlined=outlined)[index]
    image, result = fit(case)
    assert_accepted(case, image, result)
    accepted = [a for a in result['scene_attempts'] if a['outcome'] == 'accepted']
    assert len(accepted) == 1
    assert accepted[0]['painter_order'] == 'observed_depth'
    assert sum(a['operator'] in ('edit', 'split_edit', 'group_islands')
               for a in result['scene_attempts']) <= 96


@pytest.mark.parametrize('kind', ['rectangle', 'circle'])
@pytest.mark.parametrize('groups', [2, 3])
def test_groups_also_compose_single_primitive_inventories(kind, groups):
    case = make_cases(731429, groups=groups, outlined=True)[0]
    root = ET.fromstring(case['svg'])
    for element, obj in zip(list(root)[3:], case['expected_objects'][1:]):
        if obj['kind'] == kind:
            continue
        sw = obj['stroke_width']
        x, y, w, h = obj['bbox']
        for key in ('cx', 'cy', 'r', 'x', 'y', 'width', 'height', 'rx'):
            element.attrib.pop(key, None)
        element.tag = '{http://www.w3.org/2000/svg}'+('rect' if kind == 'rectangle' else kind)
        if kind == 'rectangle':
            element.attrib.update(x=str(x+sw/2), y=str(y+sw/2), width=str(w-sw), height=str(h-sw))
        else:
            element.attrib.update(cx=str(x+w/2), cy=str(y+w/2), r=str((w-sw)/2))
            obj['bbox'][3] = w
        obj.update(kind=kind)
        obj.pop('corner_radius', None)
    inventory = (f'Ein gefüllter Kreis und {2*groups} gefüllte Rechtecke' if kind == 'rectangle'
                 else f'{2*groups+1} gefüllte Kreise')
    case['description'] = inventory+'. '+case['description'].split('. ', 1)[1]
    case['svg'] = ET.tostring(root, encoding='unicode')
    image, result = fit(case)
    assert_accepted(case, image, result)


def test_equal_paint_in_different_groups_keeps_separate_instances():
    case = make_cases(731429, groups=2, rounded=True, outlined=True, same_fill=True)[0]
    image, result = fit(case)
    assert_accepted(case, image, result)


def test_a_rejected_connected_contract_does_not_poison_a_grouped_contract():
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy

    case = make_cases(731429, groups=2, rounded=True, outlined=True)[0]
    connected = deepcopy(case)
    connected['description'] = connected['description'].replace(
        'und bilden 2 getrennte Gruppen mit teilweisen Überdeckungen', 'und überlappen sich teilweise')
    session = ImageSearch(SearchPolicy(seconds=20, max_seconds=20))
    assert fit(connected, session)[1] is None
    assert any(session.structure_rejections.values())
    image, result = fit(case, session)
    assert_accepted(case, image, result)


@pytest.mark.parametrize('number', ['2', 'zwei'])
def test_group_count_is_part_of_the_consumed_contract(number):
    text = make_cases(groups=2)[0]['description'].replace('2 getrennte Gruppen', number+' getrennte Gruppen')
    contract = mixed.scene_contract(text)
    assert contract is not None and contract['overlap_groups'] == 2


@pytest.mark.parametrize('claim', [' Mit Text.', ' Die Formen sind getrennt.',
    ' Eine zusätzliche Linie.', ' Die Gruppen überlappen sich.',
    ' Die Kreise haben gerundete Ecken.'])
def test_group_clause_does_not_discard_other_assertions(claim):
    assert mixed.scene_contract(make_cases(groups=2)[0]['description']+claim) is None


@pytest.mark.parametrize('replacement', ['1', '5', 'drei', 'zwei oder drei'])
def test_invalid_or_impossible_group_inventory_stays_unsupported(replacement):
    text = make_cases(groups=2)[0]['description'].replace('2 getrennte Gruppen', replacement+' getrennte Gruppen')
    assert mixed.scene_contract(text) is None


@pytest.mark.parametrize('damage', ['wrong_groups', 'one_connected_group', 'missing', 'extra',
                                   'isolated_child', 'texture', 'wrong_order'])
def test_grouping_never_excuses_a_damaged_scene(damage):
    case = deepcopy(make_cases(731429, groups=3, rounded=True, outlined=True)[0])
    root = ET.fromstring(case['svg'])
    if damage == 'wrong_groups':
        case['description'] = case['description'].replace('3 getrennte Gruppen', '2 getrennte Gruppen')
    elif damage == 'one_connected_group':
        case['description'] = case['description'].replace(
            'und bilden 3 getrennte Gruppen mit teilweisen Überdeckungen', 'und überlappen sich teilweise')
    elif damage == 'missing':
        root.remove(root[-1])
    elif damage == 'extra':
        ET.SubElement(root, 'rect', x='165', y='170', width='12', height='12', fill='#123456')
    elif damage == 'isolated_child':
        root[4].set('x', '150')
    elif damage == 'texture':
        ET.SubElement(root, 'rect', x='90', y='90', width='12', height='12', fill='white')
    else:
        # Force the opposite claimed order using independently detected objects;
        # every group must keep its own observed front instance.
        from tools.run_plan_b_variations import render
        from src.iCCModules.imageCompositeConverterSearchScheduler import drain
        pixels = render(case['svg'], case['width'], case['height'])
        contract = mixed.scene_contract(case['description'])
        objects = mixed.detect_instances(pixels, contract)
        ordered = mixed.observed_painter_order(pixels, objects)
        assert drain(mixed._fit_instances_steps(case['width'], case['height'], pixels=pixels,
            contract=contract, objects=[ordered[0], *reversed(ordered[1:])], render_fn=render,
            error_fn=lambda a, b: float(abs(a.astype(float)-b).mean()))) is None
        return
    case['svg'] = ET.tostring(root, encoding='unicode')
    assert fit(case)[1] is None


@pytest.mark.parametrize('gap,accepted', [(8., True), (2., False), (0., False)])
def test_separation_requires_clear_native_rims_even_with_exact_raster_fit(gap, accepted):
    import numpy as np
    from tools.run_plan_b_variations import render
    from src.iCCModules.imageCompositeConverterSearchScheduler import drain

    # Two overlapping pairs of rectangles. Across groups the fill gap is
    # positive, but two-pixel strokes touch when that gap is only two pixels.
    boxes = [(60., 80., 45., 45.), (80., 95., 45., 45.),
             (125.+gap, 80., 45., 45.), (145.+gap, 95., 45., 45.)]
    palette = [(40., 70., 120.), (150., 60., 80.), (60., 115., 40.), (100., 65., 145.)]
    parent = dict(kind='circle', geometry=np.array([20., 10., 220., 220., 2.]),
                  colors=np.array([235., 217., 187., 179., 152., 97., 237., 240., 243.]))
    objects = [parent, *[dict(kind='rectangle', geometry=np.array([*box, 2.]),
                             colors=np.array([*paint[::-1], *paint[::-1], 237., 240., 243.]))
                        for box, paint in zip(boxes, palette)]]
    shapes = ''.join(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
                     f'fill="rgb{tuple(int(c) for c in paint)}" stroke="#f3f0ed" stroke-width="2"/>'
                     for (x, y, w, h), paint in zip(boxes, palette))
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="260" height="240">'
           '<defs><linearGradient id="p" x1="0%" y1="0%" x2="100%" y2="0%">'
           '<stop offset="0" stop-color="#bbd9eb"/><stop offset="1" stop-color="#6198b3"/>'
           '</linearGradient></defs><rect width="260" height="240" fill="white"/>'
           '<circle cx="130" cy="120" r="110" fill="url(#p)" stroke="#f3f0ed" stroke-width="2"/>'
           +shapes+'</svg>')
    contract = mixed.scene_contract('Ein gefüllter Kreis und vier gefüllte Rechtecke. '
        'Der Kreis hat einen horizontalen Farbverlauf. Die Rechtecke liegen innerhalb des Kreises '
        'und bilden zwei getrennte Gruppen mit teilweisen Überdeckungen. '
        'Die Formen haben helle Konturen. Keine Beschriftung.')
    result = drain(mixed._fit_instances_steps(260, 240, pixels=render(svg, 260, 240),
        contract=contract, objects=objects, render_fn=render,
        error_fn=lambda a, b: float(abs(a.astype(float)-b).mean())))
    assert (result is not None) == accepted
