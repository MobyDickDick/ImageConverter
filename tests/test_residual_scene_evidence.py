"""A no-output timeout remains a verified failure, never a hidden success."""
import json
from pathlib import Path
import shutil

import pytest

from tools.evaluate_layered_scene import verify_report

ROOT = Path(__file__).resolve().parents[1]/'artifacts/evaluation/residual_scene_v1'


def test_saved_final_outputs_include_the_failed_timeout_in_the_denominator():
    report = verify_report(ROOT/'final-input', ROOT/'final', write_verification=False)
    assert (report['accepted'], report['completed']) == (7, 9)
    assert report['cases'][6]['absence_reason'] == 'time_limit_no_output'
    assert not report['cases'][6]['accepted']


@pytest.mark.parametrize('damage', ['accepted', 'budget', 'access', 'output', 'not_timeout'])
def test_missing_output_needs_negative_decision_and_independent_timeout_evidence(tmp_path, damage):
    output = tmp_path/'trial'
    shutil.copytree(ROOT/'final', output)
    folder = output/'residual_06/conversion/reports'
    path = output/'report.json' if damage == 'accepted' else folder/('residual_06_reference_access.json' if damage == 'access' else 'residual_06_deadline.json')
    data = json.loads(path.read_text(encoding='utf-8'))
    if damage == 'accepted':
        data['cases'][6]['accepted'] = True
    elif damage == 'budget':
        data['max_seconds'] = 60.
    elif damage == 'access':
        data['blocked_svg_reads'] = ['foreign.svg']
    elif damage == 'not_timeout':
        data['stop_reason'] = 'execution_error'
    else:
        target = output/'residual_06/conversion/converted_svgs/unreported.svg'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('<svg/>', encoding='utf-8')
    path.write_text(json.dumps(data), encoding='utf-8')
    with pytest.raises(ValueError):
        verify_report(ROOT/'final-input', output, write_verification=False)
