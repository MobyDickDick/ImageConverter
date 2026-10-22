"""Saved real pixels/vectors remain bound to independently computed gates."""
import json
from pathlib import Path

import pytest

from tools.evaluate_gradient_scene_acceptance import evaluate

EVIDENCE = Path(__file__).resolve().parents[1]/'artifacts/evaluation/gradient_scene_v1'


def test_original_pairs_pass_both_gates_with_measured_semantics():
    manifest = json.loads((EVIDENCE/'manifest.json').read_text(encoding='utf-8'))
    result = evaluate(manifest, EVIDENCE)['satisfaction_gate']
    assert result['summary']['satisfactory'] == 2
    for case in result['cases']:
        assert case['before']['semantic_score'] == 0
        assert case['after']['semantic_score'] == 1
        assert not case['regressed_metrics']
        assert case['quality_complexity_gate']['passed']
        assert case['good_solution_gate']['status'] == 'good'


@pytest.mark.parametrize('field', ['source_sha256', 'after_svg_sha256', 'before_svg_sha256'])
def test_changed_source_or_saved_output_cannot_retain_acceptance(field):
    manifest = json.loads((EVIDENCE/'manifest.json').read_text(encoding='utf-8'))
    manifest['cases'][0][field] = 'changed'
    with pytest.raises(ValueError, match='hash mismatch'):
        evaluate(manifest, EVIDENCE)


def test_wrong_object_oracle_rejects_complete_pair():
    manifest = json.loads((EVIDENCE/'manifest.json').read_text(encoding='utf-8'))
    manifest['cases'][0]['expected_objects'][0]['gradient_axis'] = 1
    result = evaluate(manifest, EVIDENCE)['satisfaction_gate']
    assert result['summary']['satisfactory'] == 1
    assert not result['cases'][0]['satisfactory']
