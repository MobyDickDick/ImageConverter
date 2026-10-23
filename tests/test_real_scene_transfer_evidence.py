"""A failed real transfer stays negative and independently reproducible."""
import hashlib
import json
from pathlib import Path
import shutil

import pytest

from tools.verify_real_scene_transfer_evidence import verify


EVIDENCE = Path(__file__).resolve().parents[1]/'artifacts/evaluation/real_scene_transfer_v1'


def hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


def test_real_transfer_is_negative_and_verification_is_read_only():
    before = hashes(EVIDENCE)
    result = verify(EVIDENCE/'manifest.json')
    assert result['accepted'] == 0
    assert result['total'] == 2
    assert result['task_complete'] is False
    assert result['retuned_after_trial'] is False
    assert result['executes_converter'] is False
    assert result['historical_catalogue_exposure'] is True
    assert all(c['source'] is None for c in result['cases'])
    assert hashes(EVIDENCE) == before


@pytest.mark.parametrize('damage', [
    'svg', 'missing_trial', 'decision', 'oracle', 'runtime', 'seed', 'budget', 'access',
])
def test_corrupt_or_falsely_positive_transfer_evidence_is_rejected(tmp_path, damage):
    root = tmp_path/'transfer'
    shutil.copytree(EVIDENCE, root)
    path = root/'manifest.json'
    manifest = json.loads(path.read_text(encoding='utf-8'))
    report_path = root/'trial/report.json'
    report = json.loads(report_path.read_text(encoding='utf-8'))
    case = report['cases'][0]
    if damage == 'svg':
        (root/'trial'/case['output_svg']).write_text('<svg/>', encoding='utf-8')
        # The file seal catches output replacement before attempting rendering.
        with pytest.raises(ValueError, match='changed evidence'):
            verify(path)
        return
    if damage == 'missing_trial':
        report['cases'].pop()
    elif damage == 'decision':
        case['accepted'] = True
    elif damage == 'oracle':
        oracle = root/'annotations.json'
        data = json.loads(oracle.read_text(encoding='utf-8'))
        data['cases'][0]['expected_objects'].pop()
        oracle.write_text(json.dumps(data), encoding='utf-8')
    elif damage == 'runtime':
        report['source_sha256'] = {}
    elif damage == 'seed':
        report['seed'] = 42
    else:
        folder = root/'trial'/case['case_id']
        if damage == 'budget':
            p = folder/'conversion/reports/conversion_result_map.json'
            rows = json.loads(p.read_text(encoding='utf-8'))
            next(iter(rows.values()))['params']['adaptive_search']['max_seconds'] = 60
        else:
            p = folder/'reference_access.json'
            rows = json.loads(p.read_text(encoding='utf-8'))
            rows['blocked_svg_reads'] = ['forbidden-reference.svg']
        p.write_text(json.dumps(rows), encoding='utf-8')
    report_path.write_text(json.dumps(report), encoding='utf-8')
    # Refresh outer file checksums deliberately: the independent semantic,
    # freeze, worker-access and budget checks must still reject false evidence.
    manifest['files'] = {k: v for k, v in hashes(root).items()
                         if k not in ('manifest.json', 'README.md')}
    path.write_text(json.dumps(manifest), encoding='utf-8')
    with pytest.raises(ValueError):
        verify(path)
