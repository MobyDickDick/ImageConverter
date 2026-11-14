"""Native edge ownership, retained real marks, and frozen independent inventory."""
import copy
import json
from xml.etree import ElementTree as ET

import pytest

from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy, image_search
from src.iCCModules.imageCompositeConverterFallbackComposition import residual_line_owner, edits
from src.iCCModules.imageCompositeConverterFallbackStructure import explore_structures
from tools.check_segment_scene import check_scene
from tools.evaluate_fallback_cleanup import EVIDENCE, verified, controls
from tools.evaluate_fallback_composition import review
from tools.run_plan_b_variations import render

MANIFEST = verified()
CASES = MANIFEST['cases']
NS = '{http://www.w3.org/2000/svg}'


def line(x1, y1, x2, y2):
    return ET.Element(NS+'line', x1=str(x1), y1=str(y1), x2=str(x2), y2=str(y2),
                      stroke='#c7c7c7', **{'stroke-width':'1'})


def grouped(body, attrs=None):
    root = ET.Element(NS+'svg', width='144', height='144', viewBox='0 0 144 144')
    ET.SubElement(root, NS+'rect', width='144', height='144', fill='white')
    group = ET.SubElement(root, NS+'g', attrs or {}, **{'data-fallback-group':'example'})
    group.extend(ET.fromstring('<g>'+body+'</g>'))
    for index, node in enumerate(group):
        node.set('data-part', str(index))
    return ET.tostring(root, encoding='unicode')


@pytest.mark.parametrize('candidate', [line(10,48,34,48), line(34,48,34,24), line(10,26,10.8,44),
                                       line(34,24,15,24), line(10,24,34,48)])
def test_contour_and_diagonal_retracing_is_identified_without_using_paint_color(candidate):
    svg = grouped('<rect x="10" y="24" width="24" height="24" stroke="#888888"/>'
                  '<line x1="10" y1="24" x2="34" y2="48" stroke="#eeeeee"/>')
    assert residual_line_owner(svg,candidate)['coverage'] >= .9


@pytest.mark.parametrize('candidate', [line(13,32,31,32), line(6,50,38,50), line(34,48,75,48),
                                       line(10,24,10,64), line(10,24,34,32)])
def test_new_interior_parallel_extended_and_crossing_lines_are_not_owned(candidate):
    svg = grouped('<rect x="10" y="24" width="24" height="24" stroke="#888888"/>')
    assert residual_line_owner(svg,candidate) is None


@pytest.mark.parametrize('attrs', [{'transform':'translate(10 0)'}, {'style':'stroke-width:5'},
                                  {'opacity':'.5'}, {'clip-path':'url(#clip)'}, {'stroke-width':'5'}])
def test_unsupported_inherited_geometry_never_supplies_ownership(attrs):
    assert residual_line_owner(grouped('<line x1="10" y1="24" x2="34" y2="24" stroke="gray"/>',attrs),
                               line(10,24,34,24)) is None


def test_svg_lengths_and_definitions_are_not_guessed_as_viewport_edges():
    assert residual_line_owner(grouped('<line x1="10%" y1="24" x2="34" y2="24" stroke="gray"/>'),
                               line(10,24,34,24)) is None
    assert residual_line_owner(grouped('<defs><line x1="10" y1="24" x2="34" y2="24" stroke="gray"/></defs>'),
                               line(10,24,34,24)) is None
    svg = grouped('<line x1="10" y1="24" x2="34" y2="24" stroke="gray"/>')
    root = ET.fromstring(svg)
    root.set('viewBox','0 0 72 72')
    assert residual_line_owner(ET.tostring(root,encoding='unicode'),line(10,24,34,24)) is None


@pytest.mark.parametrize('case', CASES, ids=lambda c:c['case_id'])
def test_actual_combined_search_has_complete_independent_inventory_and_keeps_context(case):
    image = render(case['svg'],144,144)
    session = ImageSearch(SearchPolicy(seconds=5,max_seconds=5))
    with image_search(session):
        fitted, report = explore_structures(case['seed_svg'],image,render(case['seed_svg'],144,144),
                                           render,session,{},mode='combined')
    checked = check_scene(fitted['svg'],case['annotation'])
    assert checked['complete'], checked
    assert not checked['hidden_geometry_verified']
    assert checked['omitted_hidden_geometry'] == ['linkage']
    assert all(r['complete'] for r in review(image,fitted['svg'],case).values())
    assert report['probe_count'] <= 32
    assert report['render_evaluations'] == session.evaluations
    assert not session.validated
    rejected = [r for r in report['proposals'] if r.get('rejection') == 'existing_group_edge']
    assert rejected and all('error' not in r and not r['accepted'] for r in rejected)
    old = {n.get('id'):ET.tostring(n) for n in ET.fromstring(case['seed_svg']) if n.get('id','').startswith('keep-')}
    actual = {n.get('id'):ET.tostring(n) for n in ET.fromstring(fitted['svg']) if n.get('id') in old}
    assert actual == old
    for damage, svg in controls(fitted['svg']):
        assert not check_scene(svg,case['annotation'])['complete'], damage


def test_repair_precedes_overlay_and_still_offers_addition_if_repair_fails():
    seed = '<svg xmlns="http://www.w3.org/2000/svg"><rect id="old" x="10" y="24" width="24" height="24" fill="blue"/></svg>'
    group = ET.fromstring(grouped('<rect x="10" y="24" width="24" height="24" stroke="gray"/>'))[1]
    candidates = list(edits(seed,group,144,144))
    assert [op for _,op in candidates] == ['replace','add']
    assert 'id="old"' not in candidates[0][0]
    assert 'id="old"' in candidates[1][0]


def test_new_raster_supported_line_inside_group_bounds_is_still_added():
    # A rectangular group has ample interior away from its four contours.
    seed = grouped('<rect x="10" y="24" width="70" height="70" fill="#2288bb" stroke="#888888"/>')
    root = ET.fromstring(seed)
    mark = line(24,46,64,46)
    mark.set('stroke','#eeeeee')
    mark.set('stroke-width','2')
    root.append(mark)
    image = render(ET.tostring(root,encoding='unicode'),144,144)
    session = ImageSearch(SearchPolicy(seconds=5,max_seconds=5))
    with image_search(session):
        fitted, report = explore_structures(seed,image,render(seed,144,144),render,session,{},mode='combined')
    before = render(seed,144,144)[43:50,24:64].astype(float)
    after = fitted['rendered'][43:50,24:64].astype(float)
    target = image[43:50,24:64].astype(float)
    assert ((target-after)**2).mean() < ((target-before)**2).mean()*.2
    assert any(r['accepted'] and 'residual_line_group' in r['origin'] for r in report['proposals'])


def test_manifest_and_previous_checker_are_sealed(tmp_path):
    from tools.evaluate_fallback_cleanup import verified
    import shutil
    folder = tmp_path/'freeze'
    shutil.copytree(EVIDENCE,folder)
    manifest = copy.deepcopy(MANIFEST)
    manifest['cases'][0]['annotation']['objects'].pop()
    (folder/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
    with pytest.raises(ValueError,match='Changed cleanup manifest'):
        verified(folder)


def test_saved_results_are_hash_bound_and_pass_the_original_inventory_contract():
    from tools.evaluate_fallback_cleanup import digest
    seal = json.loads((EVIDENCE/'results/seal.json').read_text(encoding='utf-8'))
    for name, sha in seal['files'].items():
        assert digest(EVIDENCE/'results'/name) == sha
    for folder in ['current','cli']:
        for path in (EVIDENCE/'results'/folder).glob('*.svg'):
            case = next(c for c in CASES if path.stem.startswith(c['case_id']))
            assert check_scene(path.read_text(encoding='utf-8'),case['annotation'])['complete']
