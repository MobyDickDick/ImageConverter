"""The wording experiment must retain failures and independently recheck evidence."""
import json

import pytest
from PIL import Image

from tools import evaluate_semantic_robustness as evaluation


def test_summary_counts_families_instead_of_formulations():
    records = [dict(case_id=f'p{i}', family='example', kind='positive', passed=i!=4,
                    claimed_success=i!=4) for i in range(5)]
    records += [dict(case_id=f'n{i}', family='example', kind='object_count', passed=i!=2,
                     claimed_success=i==2) for i in range(3)]
    summary = evaluation.summarize(records)
    assert summary['attempts'] == 8
    assert summary['positives'] == 5 and summary['positive_passes'] == 4
    assert summary['negatives'] == 3 and summary['safe_rejections'] == 2
    assert summary['accepted_families'] == 0
    assert summary['families'][0]['silent_negative_successes'] == 1


def test_region_check_catches_deleted_small_foreground():
    from tools.run_plan_b_variations import render
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="60" height="60">'
           '<rect width="60" height="60" fill="white"/>'
           '<circle cx="30" cy="30" r="25" fill="#aabbcc"/>'
           '<rect x="27" y="27" width="6" height="6" fill="black"/></svg>')
    case = dict(width=60, height=60, expected_text='', expected_circles=1,
                regions=[dict(name='small_mark', box=[.4,.4,.2,.2])])
    pixels = render(svg, 60, 60)
    limits = dict(normalized_mse=.03, edge_score=.55)
    assert evaluation.check_output(case, pixels, svg, limits)['passed']
    broken = svg.replace('<rect x="27" y="27" width="6" height="6" fill="black"/>','')
    result = evaluation.check_output(case, pixels, broken, limits)
    assert not result['regions'][0]['passed']
    assert not result['passed']


def test_native_text_case_is_part_of_contract():
    from tools.run_plan_b_variations import render
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40">'
           '<circle cx="20" cy="20" r="18" fill="white" stroke="black"/>'
           '<text x="10" y="26" font-size="17">rF</text></svg>')
    case = dict(width=40, height=40, expected_text='rF', expected_circles=1, regions=[])
    pixels = render(svg,40,40)
    result = evaluation.check_output(case, pixels, svg.replace('>rF<','>rf<'), {})
    assert not result['structure']['passed']


def test_frozen_manifest_and_raster_changes_are_rejected(tmp_path):
    (tmp_path/'rasters').mkdir()
    image = tmp_path/'rasters/input.png'
    Image.new('RGB',(10,10),'white').save(image)
    manifest = dict(cases=[dict(case_id='item00p0', image='rasters/input.png', input_sha256=evaluation.digest(image))])
    evaluation.write_json(tmp_path/'manifest.json',manifest)
    evaluation.write_json(tmp_path/'freeze.json',{'manifest.json':evaluation.digest(tmp_path/'manifest.json'),
                                                'rasters/input.png':evaluation.digest(image)})
    assert evaluation.verify_inputs(tmp_path)==manifest
    with image.open('ab') as handle:
        handle.write(b'changed')
    with pytest.raises(ValueError, match='changed'):
        evaluation.verify_inputs(tmp_path)


def test_checked_in_cases_have_ten_real_topologies_and_predeclared_wording():
    config=json.loads(evaluation.DEFAULT_SELECTION.read_text(encoding='utf-8'))
    families=config['families']
    assert len(families)==len({f['family'] for f in families})==10
    for family in families:
        assert len(family['descriptions'])==len(set(family['descriptions']))==5
        assert {n['kind'] for n in family['negatives']} == {'object_count','text_conflict','unresolved_relation'}
        assert family['regions']
        assert all('AC0' not in text and 'GE0' not in text for text in family['descriptions'])
