"""Independent complete inventory, native contacts, transforms and occlusion."""
import ast
import copy
import json
from xml.etree import ElementTree as ET

import pytest

from tools.check_native_scene import check_scene, extract, transform
from tools.evaluate_fallback_checker import SOURCE, controls, development_cases, freeze, verify

CASES = list(development_cases())
BASE = CASES[0]


@pytest.mark.parametrize('case', CASES, ids=lambda c:c['case_id'])
def test_complete_native_inventory_and_relations_pass(case):
    result = check_scene(case['svg'],case['annotation'])
    assert result['complete'], result
    assert len(result['mapping']) == 14
    assert all(r['passed'] for r in result['relations'])


@pytest.mark.parametrize('case', CASES, ids=lambda c:c['case_id'])
@pytest.mark.parametrize('damage', [d for d,_ in controls(BASE)])
def test_independent_checker_rejects_each_scene_defect(case,damage):
    svg = dict(controls(case))[damage]
    result = check_scene(svg,case['annotation'])
    assert result['supported'], result
    assert not result['complete']
    if damage == 'wrong_connection':
        assert result['reason'] == 'assignment_or_relations'
        assert not next(r for r in result['relations'] if r['kind']=='endpoints_on_boundaries')['passed']
    if damage == 'wrong_depth':
        assert result['reason'] == 'assignment_or_relations'


def test_runtime_roles_and_ids_cannot_supply_or_spoof_any_object_or_relation():
    root = ET.fromstring(BASE['svg'])
    for i,node in enumerate(root.iter()):
        node.set('id',f'arbitrary-{i}')
        node.set('data-fallback-group','forged-group')
        node.set('data-part','forged-part')
    assert check_scene(ET.tostring(root,encoding='unicode'),BASE['annotation'])['complete']
    # Importing a converter or the previous evaluator into this module would
    # invalidate the independence boundary, even if the import is later unused.
    tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
    for node in ast.walk(tree):
        if isinstance(node,ast.ImportFrom):
            assert not (node.module or '').startswith(('src','tools'))
        if isinstance(node,ast.Import):
            assert all(not n.name.startswith(('src','tools')) for n in node.names)
        assert not isinstance(node,ast.Call) or not isinstance(node.func,ast.Name) or node.func.id not in {'__import__','eval','exec'}


def test_equivalent_nested_transforms_paint_inheritance_and_vertex_order():
    root = ET.fromstring(BASE['svg'])
    group = root[1]
    inner = ET.Element('{http://www.w3.org/2000/svg}g', transform='translate(-3 -7)')
    group.set('transform','translate(3 7)')
    for child in list(group):
        group.remove(child)
        inner.append(child)
    group.append(inner)
    head = inner[9]
    head.set('points','105,73 111,60 99,60')
    inner.set('fill','#cc2255')
    head.attrib.pop('fill')
    # Other defaults must retain their original appearance.
    for child in inner:
        if child.tag.endswith('line'):
            child.set('fill','none')
    assert check_scene(ET.tostring(root,encoding='unicode'),BASE['annotation'])['complete']


@pytest.mark.parametrize('fragment', [
    '<path d="M 1 1 L 2 2"/>', '<use href="#anything"/>', '<image href="file:///tmp/x"/>',
    '<text x="2" y="3">X</text>', '<defs><circle r="2"/></defs>',
    '<ellipse cx="10" cy="10" rx="4" ry="2"/>', '<script/>',
    '<circle cx="2" cy="2" r="1" style="fill:red"/>',
    '<circle cx="2" cy="2" r="1" opacity="0"/>',
    '<rect x="1" y="1" width="2" height="2" rx="1"/>',
    '<circle cx="2" cy="2" r="1" clip-path="url(#a)"/>',
    '<circle cx="2" cy="2" r="1" fill="url(#gradient)"/>',
    '<circle cx="2" cy="2" r="1" fill="rgba(0,0,0,0)"/>',
    '<foreign:circle xmlns:foreign="urn:other" cx="2" cy="2" r="1"/>',
    '<circle cx="2" cy="2" r="NaN"/>', '<circle cx="2" cy="2" r="1e999"/>',
])
def test_unsupported_semantics_never_receive_a_positive_verdict(fragment):
    svg = BASE['svg'].replace('</svg>',fragment+'</svg>')
    result = check_scene(svg,BASE['annotation'])
    assert not result['complete'] and not result['supported']


@pytest.mark.parametrize('tx', ['scale(0)', 'scale(2 1)', 'matrix(1 0 1 1 0 0)',
                               'translate(1) junk', 'rotate(nan)', 'skewX(15)', 'scale(.00001 .0001)'])
def test_unsupported_or_malformed_transforms_fail_closed(tx):
    with pytest.raises(ValueError):
        transform(tx)


@pytest.mark.parametrize('edit', ['incomplete','duplicate_id','unknown_relation','bad_tolerance','unknown_object'])
def test_incomplete_or_invalid_external_annotations_fail_closed(edit):
    ann = copy.deepcopy(BASE['annotation'])
    if edit == 'incomplete':
        ann['complete_inventory'] = False
    elif edit == 'duplicate_id':
        ann['objects'][1]['id'] = ann['objects'][0]['id']
    elif edit == 'unknown_relation':
        ann['relations'][0]['kind'] = 'runtime_group_says_ok'
    elif edit == 'bad_tolerance':
        ann['limits']['position'] = float('nan')
    else:
        ann['relations'][0]['objects'][0] = 'absent'
    assert not check_scene(BASE['svg'],ann)['supported']


def test_one_primitive_cannot_satisfy_two_expected_objects_even_with_same_total_count():
    ann = copy.deepcopy(BASE['annotation'])
    ann['objects'][1] = dict(ann['objects'][2], id='context_circle')
    result = check_scene(BASE['svg'],ann)
    assert not result['complete']
    assert result['reason'] == 'assignment_or_relations'


def test_limits_viewport_xml_and_native_object_count():
    assert not check_scene(BASE['svg'].replace('viewBox="0 0 144 144"','viewBox="0 0 72 72"'),BASE['annotation'])['supported']
    assert not check_scene('<!DOCTYPE svg>'+BASE['svg'],BASE['annotation'])['supported']
    assert not check_scene('<svg',BASE['annotation'])['supported']
    huge = BASE['svg'].replace('</svg>','<circle cx="3" cy="4" r="2"/>'*49+'</svg>')
    with pytest.raises(ValueError, match='48'):
        extract(huge,[144,144])


def test_separate_checker_freeze_refuses_overwrites_and_detects_tampering(tmp_path):
    folder = tmp_path/'frozen'
    freeze(folder)
    assert verify(folder)['real_reserves_executed'] is False
    with pytest.raises(FileExistsError):
        freeze(folder)
    (folder/'checker.py').write_text('# changed',encoding='utf-8')
    with pytest.raises(ValueError,match='Changed frozen'):
        verify(folder)


def test_checked_in_checker_and_annotation_seal_match_executed_code():
    manifest = verify()
    assert manifest['real_release_ready'] is False
    assert {'curved_real_geometry_oracle','human_annotation_audit'} <= set(manifest['missing_requirements'])


def test_historical_outputs_are_hash_bound_and_not_claimed_as_complete_native_scenes():
    from tools.evaluate_fallback_checker import EVIDENCE, digest
    evidence = json.loads((EVIDENCE/'summary.json').read_text(encoding='utf-8'))
    assert len(evidence['historical']) == 18
    assert all(row['check']['complete'] for row in evidence['historical_targets'])
    assert not any(row['check']['complete'] for row in evidence['historical'])
    assert set(p.name for p in (EVIDENCE/'historical').glob('*.svg')) == {r['file'] for r in evidence['historical']}
    for row in evidence['historical']:
        assert digest(EVIDENCE/'historical'/row['file']) == row['output_sha256']


def test_all_real_reserve_manifests_remain_sealed_and_unrun():
    from tools.freeze_real_composition_holdouts import verify as verify_reserve
    from tools.evaluate_fallback_checker import EVIDENCE
    for name in ['fallback_groups_v1','real_composition_holdout_freeze_v1']:
        result = verify_reserve(EVIDENCE.parent/name/'freeze/manifest.json')
        assert result['status'] == 'sealed_unrun' and result['converter_executed'] is False
