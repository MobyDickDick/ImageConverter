import json

import pytest

from tools import recheck_satisfactory_archive as archive_tool


@pytest.mark.parametrize('failing_variant', [None, 'beta_S'])
def test_partitioning_keeps_families_and_preserves_quality_failures(tmp_path, monkeypatch, failing_variant):
    archive = tmp_path/'archive'
    archive.mkdir()
    cases = [{'variant': name, 'execution_mode': 'semantic-only', 'image': name+'.jpg', 'svg': name+'.svg'}
             for name in ('alpha_M', 'alpha_S', 'beta_M', 'beta_S', 'gamma')]
    original = json.dumps({'case_count': len(cases), 'cases': cases})
    (archive/'index.json').write_text(original, encoding='utf-8')
    (archive/'descriptions.xml').write_text('<root/>', encoding='utf-8')
    workers = []

    def recheck(snapshot, output):
        index = json.loads((snapshot/'index.json').read_text(encoding='utf-8'))
        workers.append([case['variant'] for case in index['cases']])
        assert (snapshot/'descriptions.xml').read_text(encoding='utf-8') == '<root/>'
        for case in index['cases']:
            assert case['image'] == str((archive/(case['variant']+'.jpg')).resolve())
        results = [{'variant': case['variant'], 'passed': case['variant'] != failing_variant}
                   for case in index['cases']]
        return {'cases': results, 'case_count': len(results),
                'passed': sum(case['passed'] for case in results), 'higher_mean_delta2': []}

    monkeypatch.setattr(archive_tool, 'recheck', recheck)
    report = archive_tool.recheck_partitioned(archive, tmp_path/'output', 2)
    assert workers == [['alpha_M', 'alpha_S'], ['beta_M', 'beta_S'], ['gamma']]
    assert report['case_count'] == 5
    assert report['passed'] == (5 if failing_variant is None else 4)
    assert (archive/'index.json').read_text(encoding='utf-8') == original


def test_partitioning_rejects_lost_results(tmp_path, monkeypatch):
    archive = tmp_path/'archive'
    archive.mkdir()
    (archive/'index.json').write_text(json.dumps({'cases': [
        {'variant': 'alpha', 'execution_mode': 'semantic-only', 'image': 'input.jpg', 'svg': 'output.svg'}]}))
    (archive/'descriptions.xml').write_text('<root/>')
    monkeypatch.setattr(archive_tool, 'recheck', lambda *args: {
        'cases': [], 'case_count': 0, 'passed': 0, 'higher_mean_delta2': []})
    with pytest.raises(ValueError, match='lost or duplicated'):
        archive_tool.recheck_partitioned(archive, tmp_path/'output', 2)


def test_partitioning_retains_cross_family_compatibility_context(tmp_path, monkeypatch):
    archive = tmp_path/'archive'
    archive.mkdir()
    cases = [{'variant': name, 'execution_mode': mode, 'image': name+'.jpg', 'svg': name+'.svg'}
             for name, mode in [('alpha', 'standard'), ('beta', 'semantic-only'),
                                ('gamma', 'standard'), ('zeta', 'semantic-only')]]
    (archive/'index.json').write_text(json.dumps({'cases': cases}))
    (archive/'descriptions.xml').write_text('<root/>')
    workers = []

    def recheck(snapshot, output):
        rows = json.loads((snapshot/'index.json').read_text())['cases']
        workers.append([case['variant'] for case in rows])
        return {'cases': [{'variant': case['variant'], 'passed': True} for case in rows],
                'case_count': len(rows), 'passed': len(rows), 'higher_mean_delta2': []}

    monkeypatch.setattr(archive_tool, 'recheck', recheck)
    assert archive_tool.recheck_partitioned(archive, tmp_path/'output', 2)['passed'] == 4
    assert workers == [['beta', 'zeta'], ['alpha', 'gamma']]
