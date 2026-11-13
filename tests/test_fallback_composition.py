"""Mixed groups, retained scene objects, atomic edits and shared search limits."""
import json
from xml.etree import ElementTree as ET

import pytest

from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy, image_search
from src.iCCModules.imageCompositeConverterFallbackComposition import edits, removals, retained_paint
from src.iCCModules.imageCompositeConverterFallbackGroups import check_relations, check_parts, part_regions
from src.iCCModules.imageCompositeConverterFallbackStructure import explore_structures
from tools.evaluate_fallback_composition import EVIDENCE, digest, review, damaged_variants
from tools.run_plan_b_variations import render

MANIFEST=json.loads((EVIDENCE/'manifest.json').read_text(encoding='utf-8'))
CASES=MANIFEST['cases']


def fit(case, mode='combined', session=None, renderer=render, max_probes=32, assertions=None):
    image=render(case['svg'],144,144)
    session=session or ImageSearch(SearchPolicy(seconds=5,max_seconds=5))
    with image_search(session):
        selected, report=explore_structures(case['seed_svg'],image,render(case['seed_svg'],144,144),
                    renderer,session,assertions or {},mode=mode,max_probes=max_probes)
    return image,selected,report,session


@pytest.mark.parametrize('mode',['groups','combined'])
@pytest.mark.parametrize('case',CASES,ids=lambda c:c['case_id'])
def test_two_different_groups_compose_and_keep_existing_objects(case,mode):
    image,result,report,session=fit(case,mode)
    assert all(r['complete'] for r in review(image,result['svg'],case).values())
    root=ET.fromstring(result['svg'])
    originals={n.get('id'):ET.tostring(n) for n in ET.fromstring(case['seed_svg']).iter() if n.get('id','').startswith('keep-')}
    actual={n.get('id'):ET.tostring(n) for n in root.iter() if n.get('id') in originals}
    assert actual==originals
    assert len(check_relations(result['svg']))==2
    assert all(r['passed'] for r in check_relations(result['svg']))
    assert all(r['passed'] for r in check_parts(image,result['rendered'],part_regions(result['svg'],144,144)))
    assert report['probe_count']<=32 and report['render_evaluations']==session.evaluations
    assert not session.validated and not report['model_confirmed']
    accepted=[p['origin'] for p in report['proposals'] if p['accepted']]
    assert any(':add:' in p for p in accepted)
    if 'wrong-arrow' in case['seed_svg']:
        assert any(':replace:' in p for p in accepted)
    if 'id="extra"' in case['seed_svg']:
        assert 'id="extra"' not in result['svg']
        assert 'native_object_group:remove' in accepted


@pytest.mark.parametrize('damage',['missing_group','missing_context','wrong_connection','missing_head','extra_object'])
def test_fixed_scene_checker_rejects_missing_additional_objects_and_wrong_connections(damage):
    case=CASES[0]
    image,result,_,_=fit(case)
    svg=dict(damaged_variants(result['svg']))[damage]
    assert all(not r['complete'] for r in review(image,svg,case).values())
    if damage in {'wrong_connection','missing_head'}:
        assert not all(r['passed'] for r in check_relations(svg))


def test_composition_does_not_start_a_render_after_deadline_or_exceed_probe_cap():
    now=[0.]
    session=ImageSearch(SearchPolicy(seconds=1,max_seconds=1),clock=lambda:now[0])
    def slow(svg,w,h):
        assert now[0]<1
        now[0]+=.4
        return render(svg,w,h)
    _,_,report,_=fit(CASES[4],session=session,renderer=slow)
    assert session.evaluations==report['probe_count']==3
    assert report['stop_reason']=='time_limit'
    _,_,report,session=fit(CASES[4],max_probes=2)
    assert report['probe_count']==session.evaluations==2
    assert report['stop_reason']=='probe_limit'


def test_counts_are_checked_before_any_composition_render():
    _,_,report,session=fit(CASES[0],mode='groups',assertions={'counts':[{'kind':'polygon','count':0}]})
    assert all('error' not in p for p in report['proposals'] if p.get('rejection')=='description_assertions')
    assert any(p.get('rejection')=='description_assertions' for p in report['proposals'])


def test_correct_small_objects_cannot_be_erased_for_a_large_global_gain():
    case=CASES[0]
    image=render(case['svg'],144,144)
    root=ET.fromstring(case['svg'])
    root.remove(next(n for n in root if n.get('id')=='keep-line'))
    assert not retained_paint(image,image,render(ET.tostring(root,encoding='unicode'),144,144))


def test_nested_replacement_keeps_definitions_and_unrelated_objects():
    case=CASES[1]
    _,result,_,_=fit(case)
    group=next(n for n in ET.fromstring(result['svg']) if n.get('data-fallback-group')=='shaft_triangle')
    seed=ET.fromstring(case['seed_svg'])
    namespace='{http://www.w3.org/2000/svg}'
    defs=ET.SubElement(seed,namespace+'defs')
    ET.SubElement(defs,namespace+'circle',id='definition',cx='20',cy='20',r='5')
    nested=ET.SubElement(seed,namespace+'g',id='assembly')
    old=next(n for n in seed if n.get('id')=='wrong-arrow')
    seed.remove(old)
    nested.append(old)
    svg=ET.tostring(seed,encoding='unicode')
    replacement=dict((operation,candidate) for candidate,operation in edits(svg,group,144,144))['replace']
    root=ET.fromstring(replacement)
    assert next(n for n in root.iter() if n.get('id')=='definition') is not None
    assembly=next(n for n in root if n.get('id')=='assembly')
    assert len(assembly)==1 and assembly[0].get('data-fallback-group')=='shaft_triangle'
    assert all('id="definition"' in candidate for candidate in removals(svg,144,144))


def test_two_unsupported_atoms_can_be_removed_without_reintroducing_either():
    case=dict(CASES[3])
    case['seed_svg']=case['seed_svg'].replace('</svg>','<circle id="extra2" cx="84" cy="112" r="5" fill="#333333"/></svg>')
    _,result,_,_=fit(case,mode='groups')
    assert 'id="extra"' not in result['svg'] and 'id="extra2"' not in result['svg']


def test_freeze_preserves_previous_runtime_and_all_real_reserves_are_unrun():
    from tools.freeze_real_composition_holdouts import verify
    for name,expected in MANIFEST['runtime_sha256'].items():
        assert digest(EVIDENCE/'inputs'/name)==expected
    assert not MANIFEST['real_reserves_executed']
    for folder in ['fallback_groups_v1','real_composition_holdout_freeze_v1']:
        assert not verify(EVIDENCE.parent/folder/'freeze/manifest.json')['converter_executed']


def test_separate_scene_objects_do_not_enter_single_badge_semantics():
    from src.iCCModules.imageCompositeConverterSemantic import apply_semantic_badge_description_rules
    params={}
    assert not apply_semantic_badge_description_rules(desc=CASES[0]['description'],params=params)
    assert params.get('mode') != 'semantic_badge'
    params={}
    assert apply_semantic_badge_description_rules(desc='Kreis mit einem waagrechten Strich rechts',params=params)
    assert params['mode']=='semantic_badge'
