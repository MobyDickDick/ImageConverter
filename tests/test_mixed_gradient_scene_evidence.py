"""Retained failed transfer and development outputs must remain distinguishable."""
import json
from pathlib import Path
import shutil

import pytest

from tools.verify_mixed_gradient_scene_evidence import verify


EVIDENCE = Path(__file__).resolve().parents[1]/'artifacts/evaluation/mixed_gradient_scene_v1'


def test_stored_originals_pass_only_after_development():
    report = verify(EVIDENCE/'manifest.json')
    assert report['summary']['before']['accepted'] == 0
    assert report['summary']['first_transfer']['accepted'] == 0
    assert report['summary']['after_development']['accepted'] == 2
    assert report['satisfaction_gate']['summary']['satisfactory'] == 2
    assert report['new_heldout_real_families_after_tuning'] == 0
    assert report['executes_converter'] is False


@pytest.mark.parametrize('damage', ['vector', 'missing_case', 'description', 'decision', 'runtime'])
def test_inconsistent_retained_evidence_is_rejected(tmp_path, damage):
    output = tmp_path/'evidence'
    shutil.copytree(EVIDENCE, output)
    path = output/'manifest.json'
    manifest = json.loads(path.read_text(encoding='utf-8'))
    case = manifest['cases'][0]
    if damage == 'vector':
        (output/case['after_development']['path']).write_text('<svg/>', encoding='utf-8')
    elif damage == 'missing_case':
        manifest['cases'].pop()
    elif damage == 'description':
        case['description'] += ' Mit Text.'
    elif damage == 'decision':
        case['first_transfer']['accepted'] = True
    else:
        case['after_development']['cli_source_sha256'] = {}
    path.write_text(json.dumps(manifest), encoding='utf-8')
    with pytest.raises(ValueError):
        verify(path)
