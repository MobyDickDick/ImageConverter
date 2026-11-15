"""Native curve inventory, hidden defects and conservative SVG boundaries."""
import ast
import copy
import math
from xml.etree import ElementTree as ET

import numpy as np
import pytest

from tools import check_curve_scene as oracle
from tools import check_native_scene as strict
from tools.curve_checker_cases import development_cases, controls
from tools.evaluate_curve_checker import SOURCES, freeze, verify

CASES = list(development_cases())
PLAIN = CASES[0]
DAMAGE = [c['damage'] for c in controls(PLAIN)]


def xml(root):
    return ET.tostring(root, encoding='unicode')


@pytest.mark.parametrize('case', CASES, ids=lambda c:c['case_id'])
def test_external_complete_native_curve_inventory(case):
    result = oracle.check_scene(case['svg'], case['annotation'])
    assert result['complete'], result
    assert result['hidden_geometry_verified']
    assert sorted(result['mapping'].values()) == list(range(result['actual_count']))
    assert all(r['passed'] for r in result['relations'])


@pytest.mark.parametrize('case', CASES, ids=lambda c:c['case_id'])
@pytest.mark.parametrize('damage', DAMAGE)
def test_visible_and_hidden_faults_are_not_equivalent(case, damage):
    candidate = next(c['svg'] for c in controls(case) if c['damage'] == damage)
    result = oracle.check_scene(candidate, case['annotation'])
    assert not result['complete'], result
    assert not result['hidden_geometry_verified']


@pytest.mark.parametrize('kind', ['quadratic', 'cubic', 'arc'])
@pytest.mark.parametrize('mode', ['relative', 'reverse', 'nested', 'forged_roles'])
def test_equivalent_single_strokes_without_runtime_labels(kind, mode):
    case = next(c for c in CASES if c['primitive'] == kind and c['transform'] == 'plain')
    root = ET.fromstring(case['svg'])
    group = root[1]
    if mode == 'relative':
        group[1].set('d', {'quadratic':'m24 60 q24 -48 48 0',
                           'cubic':'m24 60 c12 -48 36 -48 48 0',
                           'arc':'m24 60 a24 24 0 0 1 24 -24'}[kind])
    elif mode == 'reverse':
        group[1].set('d', {'quadratic':'M72 60 Q48 12 24 60',
                           'cubic':'M72 60 C60 12 36 12 24 60',
                           'arc':'M48 36 A24 24 0 0 0 24 60'}[kind])
    elif mode == 'nested':
        child = group[1]
        group.remove(child)
        wrapper = ET.Element(oracle.NS+'g', fill='none', stroke='#224466', **{'stroke-width':'2'})
        for key in ('fill', 'stroke', 'stroke-width'):
            del child.attrib[key]
        wrapper.append(child)
        group.insert(1, wrapper)
    else:
        for node in root.iter():
            node.set('id', 'fake-runtime-success')
            node.set('data-fallback-group', 'wrong')
            node.set('data-part', 'missing')
    assert oracle.check_scene(xml(root), case['annotation'])['complete']


def test_connection_is_measured_beyond_object_matching():
    root = ET.fromstring(PLAIN['svg'])
    # Below .05 object tolerance; above the explicit .01 connection tolerance.
    root[1][0].set('x2', '24.04')
    result = oracle.check_scene(xml(root), PLAIN['annotation'])
    assert not result['complete'] and not result['unmatched_expected']
    assert not result['relations'][0]['passed']


def test_tangent_relation_checks_curve_derivative_not_control_point_chord():
    root = ET.fromstring(PLAIN['svg'])
    root[1][1].set('d', 'M24 60 Q48.04 12 72 60')
    ann = copy.deepcopy(PLAIN['annotation'])
    ann['relations'][1]['angle_tolerance'] = .01
    result = oracle.check_scene(xml(root), ann)
    assert not result['complete'] and not result['unmatched_expected']
    assert result['relations'][0]['passed'] and not result['relations'][1]['passed']


@pytest.mark.parametrize('d,center,middle,sweep', [
    ('M10 20 A10 10 0 0 1 20 10', [20,20], [20-10/math.sqrt(2),20-10/math.sqrt(2)], 90),
    ('M10 20 A10 10 0 1 0 20 10', [20,20], [20+10/math.sqrt(2),20+10/math.sqrt(2)], -270),
    ('M0 0 A1 1 0 0 1 4 0', [2,0], [2,-2], 180),
    ('M0 0 A2 1 0 0 0 4 0', [2,0], [2,1], -180),
])
def test_analytical_arc_centers_sweep_branches_and_svg_radius_correction(d, center, middle, sweep):
    actual = oracle.parse_curve(d)
    assert np.allclose(actual['center'], center)
    assert np.allclose(actual['middle'], middle)
    assert abs(actual['sweep']-sweep) < 1e-7


@pytest.mark.parametrize('d', [
    'M0 0 Q1 1 2 0 Q3 1 4 0', 'M0 0 C1 2 3 2 4 0 Z', 'M0 0 L1 1',
    'M0 0 T1 1', 'M0 0 S1 2 3 4', 'M0 0 A0 2 0 0 1 3 4',
    'M0 0 A2 2 0 2 1 3 4', 'M0 0 A2 2 0 0.0 1 3 4',
    'M0 0 A2 2 0 0 1 0 0', 'M0 0 A1e-300 2 0 0 1 3 4',
    'M0 0 Qnan 1 2 3', 'M0 0 Q1e999 1 2 3', 'M0 0 Q1 1 2 2',
    'M0 0 Q1 2 3', 'M0 0 Q1 2 3 4 garbage', 'M0 0 Q1 2 3 4;'
])
def test_unsupported_degenerate_and_malformed_paths_fail_closed(d):
    root = ET.fromstring(PLAIN['svg'])
    root[1][1].set('d', d)
    result = oracle.check_scene(xml(root), PLAIN['annotation'])
    assert not result['complete'] and not result['supported']


@pytest.mark.parametrize('attribute,value', [
    ('opacity','.5'), ('stroke-dasharray','2 2'), ('marker-end','url(#a)'),
    ('filter','url(#a)'), ('style','stroke:black'), ('x1','4'),
    ('pathLength','30'), ('transform','scale(1 2)'), ('transform','scale(0)'),
])
def test_unmodeled_svg_semantics_are_not_silently_stripped(attribute, value):
    root = ET.fromstring(PLAIN['svg'])
    root[1][1].set(attribute, value)
    result = oracle.check_scene(xml(root), PLAIN['annotation'])
    assert not result['complete'] and not result['supported']


@pytest.mark.parametrize('edit', ['incomplete','omission','loose_position','loose_angle','missing_stroke',
                                 'wrong_arc_endpoint','full_circle','unknown_relation','curve_boundary'])
def test_annotation_contract_is_explicit_bounded_and_consistent(edit):
    ann = copy.deepcopy(PLAIN['annotation'])
    if edit == 'incomplete':
        ann['complete_inventory'] = False
    elif edit == 'omission':
        ann['objects'][4]['representation'] = dict(mode='omit_hidden')
    elif edit == 'loose_position':
        ann['limits']['position'] = 3
    elif edit == 'loose_angle':
        ann['limits']['angle'] = 2
    elif edit == 'missing_stroke':
        del ann['objects'][2]['stroke']
    elif edit == 'wrong_arc_endpoint':
        ann['objects'][3]['center'][0] += 1
    elif edit == 'full_circle':
        ann['objects'][3]['sweep'] = 360
    elif edit == 'unknown_relation':
        ann['relations'].append(dict(kind='model_success', objects=['lead','curve']))
    else:
        ann['relations'].append(dict(kind='endpoint_on_boundary', objects=['lead','curve'], tolerance=.1))
    result = oracle.check_scene(PLAIN['svg'], ann)
    assert not result['complete'] and not result['supported']


def test_assignment_is_bounded_and_never_reuses_a_native_object(monkeypatch):
    monkeypatch.setattr(oracle, 'WORK_LIMIT', 2)
    result = oracle.check_scene(PLAIN['svg'], PLAIN['annotation'])
    assert not result['complete'] and result['reason'] == 'curve_assignment_limit'
    monkeypatch.setattr(oracle, 'WORK_LIMIT', 4096)
    ann = copy.deepcopy(PLAIN['annotation'])
    ann['objects'][4] = dict(ann['objects'][2], id='hidden_curve')
    assert not oracle.check_scene(PLAIN['svg'], ann)['complete']


def test_existing_straight_oracles_are_not_relaxed_and_runtime_is_not_imported():
    ann = dict(PLAIN['annotation'], schema=strict.SCHEMA)
    assert not strict.check_scene(PLAIN['svg'], ann)['complete']
    tree = ast.parse(SOURCES['checker.py'].read_text(encoding='utf-8'))
    imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    assert all(not (name or '').startswith('src') for name in imports)
    assert [n for n in imports if (n or '').startswith('tools')] == ['tools']
    assert not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                   and n.func.id in {'__import__','eval','exec'} for n in ast.walk(tree))


def test_seal_cannot_be_overwritten_and_binds_controls_annotations_and_sources(tmp_path):
    folder = tmp_path/'freeze'
    freeze(folder)
    assert len(verify(folder)['cases']) == 15
    with pytest.raises(FileExistsError):
        freeze(folder)
    (folder/'manifest.json').write_text('{}', encoding='utf-8')
    with pytest.raises(ValueError, match='Changed frozen'):
        verify(folder)


def test_checked_in_freeze_and_existing_seals_are_intact():
    from tools.evaluate_segment_checker import verify as verify_segments
    from tools.evaluate_fallback_checker import verify as verify_straight
    manifest = verify()
    assert not manifest['real_reserves_executed'] and not manifest['real_release_ready']
    assert not manifest['hidden_omission_supported']
    verify_segments()
    verify_straight()
