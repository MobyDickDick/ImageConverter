"""Logical object equivalence must not conceal missing parts or overdraw."""
import ast
import copy
from xml.etree import ElementTree as ET

import pytest

from tools import check_native_scene as strict
from tools import check_segment_scene as logical
from tools.evaluate_segment_checker import (SOURCE, controls, development_cases,
                                             freeze, verify)

CASES = list(development_cases())
SPLIT = next(c for c in CASES if c['case_id'] == 'plain-multiple_splits')


@pytest.mark.parametrize('case', CASES, ids=lambda c:c['case_id'])
def test_full_inventory_over_explicit_line_partitions(case):
    result = logical.check_scene(case['svg'], case['annotation'])
    assert result['complete'], result
    used = [i for indices in result['mapping'].values() for i in indices]
    assert sorted(used) == list(range(result['actual_count']))
    assert len(used) == len(set(used))
    assert result['hidden_geometry_verified'] == (case['representation'] == 'intact')
    assert result['work_units'] <= logical.WORK_LIMIT


@pytest.mark.parametrize('case', CASES, ids=lambda c:c['case_id'])
@pytest.mark.parametrize('damage', [d for d, _ in controls(SPLIT)])
def test_segment_and_overdraw_negatives(case, damage):
    result = logical.check_scene(dict(controls(case))[damage], case['annotation'])
    assert not result['complete'], result
    assert result.get('hidden_geometry_verified') is not True


def test_strict_checker_keeps_single_atom_contract_and_is_not_relaxed():
    ann = copy.deepcopy(SPLIT['annotation'])
    ann['schema'] = strict.SCHEMA
    assert not strict.check_scene(SPLIT['svg'], ann)['complete']


def test_no_roles_ids_or_runtime_imports_contribute_to_decision():
    root = ET.fromstring(SPLIT['svg'])
    for i, node in enumerate(root.iter()):
        node.set('id', f'forged-{i}')
        node.set('data-part', 'missing-part')
        node.set('data-fallback-group', 'forged')
    assert logical.check_scene(ET.tostring(root, encoding='unicode'), SPLIT['annotation'])['complete']
    tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
    imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    assert all(not (name or '').startswith('src') for name in imports)
    assert [name for name in imports if (name or '').startswith('tools')] == ['tools']
    assert not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                   and n.func.id in {'__import__','eval','exec'} for n in ast.walk(tree))


@pytest.mark.parametrize('edit', ['no_authorization','no_depth','no_cover','bad_cover','transparent',
                                'too_many_segments','loose_join','loose_collinearity','hidden_claim','round_cap'])
def test_external_segment_permission_and_bounded_tolerances_required(edit):
    ann = copy.deepcopy(SPLIT['annotation'])
    obj = next(o for o in ann['objects'] if o['id'] == 'linkage')
    rep = obj['representation']
    if edit == 'no_authorization':
        del obj['representation']
    elif edit == 'no_depth':
        ann['relations'] = [r for r in ann['relations'] if r['objects'] != ['joint','linkage']]
    elif edit == 'no_cover':
        rep['occluders'] = []
    elif edit == 'bad_cover':
        rep['occluders'] = ['shaft']
    elif edit == 'transparent':
        next(o for o in ann['objects'] if o['id'] == 'joint')['fill'] = 'none'
    elif edit == 'too_many_segments':
        rep['max_segments'] = 9
    elif edit == 'loose_join':
        rep['join_tolerance'] = .2
    elif edit == 'loose_collinearity':
        rep['collinearity'] = 1
    elif edit == 'hidden_claim':
        rep['hidden_geometry'] = 'verified_from_pixels'
    else:
        obj['linecap'] = 'round'
    assert not logical.check_scene(SPLIT['svg'], ann)['complete']


def test_gap_coverage_uses_actual_cover_not_expected_mask():
    root = ET.fromstring(SPLIT['svg'])
    root[1][SPLIT['slots']['joint'][0]].set('r', '2.5')
    # This is inside object-position tolerance, but exposes the internal cut.
    result = logical.check_scene(ET.tostring(root, encoding='unicode'), SPLIT['annotation'])
    assert not result['complete'] and not result['unmatched_expected']


def test_parallel_offset_segments_and_overlap_cannot_be_merged():
    for change in ('offset', 'overlap'):
        root = ET.fromstring(SPLIT['svg'])
        node = root[1][SPLIT['slots']['context_line'][1]]
        if change == 'offset':
            node.set('y1', '100.4'); node.set('y2', '100.4')
        else:
            node.set('x1', '28')
        assert not logical.check_scene(ET.tostring(root, encoding='unicode'), SPLIT['annotation'])['complete']


def test_reversed_segments_nested_inheritance_and_reordered_atoms():
    root = ET.fromstring(SPLIT['svg'])
    group = root[1]
    for name in ('linkage','context_line','partly_hidden'):
        for index in SPLIT['slots'][name]:
            node = group[index]
            a = [node.get('x1'), node.get('y1')]
            b = [node.get('x2'), node.get('y2')]
            for key,value in zip(('x1','y1','x2','y2'), b+a):
                node.set(key,value)
    a,b = SPLIT['slots']['linkage']
    group[a],group[b] = group[b],group[a]
    assert logical.check_scene(ET.tostring(root, encoding='unicode'),SPLIT['annotation'])['complete']


@pytest.mark.parametrize('work_limit,reason', [(4096,'segment_choice_limit'), (100,'segment_assignment_limit')])
def test_work_limit_fails_closed_during_ambiguous_partition_enumeration(monkeypatch,work_limit,reason):
    monkeypatch.setattr(logical,'WORK_LIMIT',work_limit)
    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
    for i in range(30):
        svg += f'<line x1="{i*3}" y1="50" x2="{i*3+2}" y2="50" stroke="black"/>'
    svg += '</svg>'
    ann = dict(schema=logical.SCHEMA, size=[100,100], complete_inventory=True,
               limits=dict(position=2,color=0,stroke_width=0), relations=[],
               objects=[dict(id='line',kind='line',points=[[0,50],[90,50]],stroke='black',
                             representation=dict(mode='collinear_segments',occluders=[],max_segments=8,
                                 join_tolerance=.05,collinearity=.1,hidden_geometry='unverified_if_omitted'))])
    result = logical.check_scene(svg,ann)
    assert not result['complete'] and result['reason'] == reason


def test_seal_binds_both_checkers_annotations_controls_and_evaluator(tmp_path):
    folder = tmp_path/'freeze'
    freeze(folder)
    assert not verify(folder)['real_release_ready']
    with pytest.raises(FileExistsError):
        freeze(folder)
    (folder/'strict_checker.py').write_text('# tampered', encoding='utf-8')
    with pytest.raises(ValueError, match='Changed frozen'):
        verify(folder)


def test_checked_in_freeze_keeps_historical_overdraw_negative():
    manifest = verify()
    assert len(manifest['historical']) == 18
    for row in manifest['historical']:
        result = logical.check_scene(row['svg'],row['annotation'])
        assert not result['complete'] and not result['unmatched_expected']
        assert result['segmented_options'] == ['linkage']
        assert 3 <= len(result['unmatched_actual']) <= 6
    assert not manifest['real_reserves_executed'] and not manifest['real_release_ready']
