"""R2 runtime inputs remain immutable; diagnostics never grant acceptance."""
import json

import pytest

from tools import evaluate_semantic_robustness as evaluation


def make_runtime(tmp_path):
    runtime = tmp_path/'runtime'
    for name, value in [('src/code.py', 'before'), ('config/model.json', '{}')]:
        path = runtime/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding='utf-8')
    return runtime


def test_all_added_removed_changed_inputs_have_both_hashes(tmp_path):
    runtime = make_runtime(tmp_path)
    before = evaluation.source_hashes(runtime)
    (runtime/'src/code.py').write_text('changed', encoding='utf-8')
    (runtime/'config/model.json').unlink()
    (runtime/'src/new.py').write_text('new', encoding='utf-8')
    with pytest.raises(ValueError, match='Runtime changed.*src/code.py'):
        evaluation.record_runtime_integrity(runtime, before, tmp_path)
    proof = json.loads((tmp_path/'runtime-integrity.json').read_text(encoding='utf-8'))
    assert proof['unchanged'] is False
    assert proof['before'] == before
    changes = proof['changes']
    assert changes['added'] == {'src/new.py': dict(before=None, after=evaluation.digest(runtime/'src/new.py'))}
    assert changes['removed'] == {'config/model.json': dict(before=before['config/model.json'], after=None)}
    assert changes['changed'] == {'src/code.py': dict(before=before['src/code.py'], after=evaluation.digest(runtime/'src/code.py'))}


@pytest.mark.parametrize('name', ['src/code.py', 'config/model.json'])
def test_real_run_rejects_code_and_config_mutations_even_on_observer_failure(tmp_path, monkeypatch, name):
    runtime = make_runtime(tmp_path)
    prepared = tmp_path/'inputs'
    prepared.mkdir()
    (prepared/'freeze.json').write_text('{}', encoding='utf-8')
    (prepared/'input.png').write_bytes(b'frozen input')
    case = dict(case_id='case', family='frozen', image='input.png', description='circle')
    monkeypatch.setattr(evaluation, 'ROOT', runtime)
    monkeypatch.setattr(evaluation, 'verify_inputs', lambda _: dict(cases=[case], region_limits={}))
    from tools import run_plan_b_variations
    def mutate(*args, **kwargs):
        (runtime/name).write_text('intentional change', encoding='utf-8')
        raise RuntimeError('observer failed')
    monkeypatch.setattr(run_plan_b_variations, 'run_case', mutate)
    output = tmp_path/'run'
    with pytest.raises(ValueError, match='Runtime changed.*'+name):
        evaluation.run(prepared, output, budget=10., only=['frozen'])
    proof = json.loads((output/'runtime-integrity.json').read_text(encoding='utf-8'))
    assert list(proof['changes']['changed']) == [name]
    assert proof['unchanged'] is False


def test_saved_proof_is_required_and_tampering_is_rejected(tmp_path):
    runtime = make_runtime(tmp_path)
    before = evaluation.source_hashes(runtime)
    report = dict(schema='semantic_robustness_run_v2', runtime_sha256=before)
    with pytest.raises(ValueError, match='Missing or changed'):
        evaluation.verify_runtime_integrity(tmp_path, report)
    report['runtime_integrity_sha256'] = evaluation.record_runtime_integrity(runtime, before, tmp_path)
    evaluation.verify_runtime_integrity(tmp_path, report)
    evidence = tmp_path/'runtime-integrity.json'
    proof = json.loads(evidence.read_text(encoding='utf-8'))
    proof['after']['src/code.py'] = 'tampered'
    evaluation.write_json(evidence, proof)
    with pytest.raises(ValueError, match='Missing or changed'):
        evaluation.verify_runtime_integrity(tmp_path, report)
    report['runtime_integrity_sha256'] = evaluation.digest(evidence)
    with pytest.raises(ValueError, match='Runtime changed'):
        evaluation.verify_runtime_integrity(tmp_path, report)
