"""Independently re-render saved CLI outputs and verify the frozen inputs."""
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.evaluate_layered_scene import verify_report

os.environ['IMAGE_CONVERTER_ISOLATE_SVG_RENDER'] = '0'
base = Path(__file__).resolve().parent
evaluation = ROOT/'artifacts/evaluation'
cohorts = [
    (base/'inputs', 'before', 0, 12, False),
    (base/'rounded_inputs', 'rounded_before', 0, 12, False),
    (base/'plan_b', 'plan_b_cli', 16, 17, False),
    (base/'inputs', 'after_final', 12, 12, True),
    (base/'rounded_inputs', 'rounded_after_final', 12, 12, True),
    (base/'additional', 'additional_cli_final', 12, 12, True),
    (base/'rounded_additional', 'rounded_additional_cli_final', 12, 12, True),
    (base/'plan_b', 'plan_b_cli_final', 17, 17, True),
    (evaluation/'overlap_composition_v1/inputs', 'existing_overlap_cli_final', 12, 12, True),
    (evaluation/'rounded_outlines_v1/inputs', 'existing_outlines_cli_final', 12, 12, True),
    (evaluation/'rounded_composition_v1/development', 'existing_rounded_cli_final', 12, 12, True),
    (evaluation/'component_splits_v1/input', 'existing_split_cli_final', 20, 20, True),
    (evaluation/'residual_scene_v1/final-input', 'existing_residual_cli_final', 7, 9, True),
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


summary = {}
for inputs, output, accepted, count, final in cohorts:
    result = verify_report(inputs, base/output, write_verification=False)
    assert (result['accepted'], result['completed']) == (accepted, count), output
    report = json.loads((base/output/'report.json').read_text(encoding='utf-8'))
    if final:
        for name, expected in report['source_sha256'].items():
            assert digest(ROOT/name.replace('\\', '/')) == expected, name
    summary[output] = dict(accepted=accepted, total=count)

comparison = json.loads((base/'regression-comparison.json').read_text(encoding='utf-8'))
for output, expected in comparison.items():
    report = json.loads((base/output/'report.json').read_text(encoding='utf-8'))
    actual = {c['case_id']: c['output_sha256'] for c in report['cases'] if c['accepted']}
    assert actual == expected['expected_output_sha256'], output

archive = ROOT/'artifacts/satisfactory_conversions'
index = json.loads((archive/'index.json').read_text(encoding='utf-8'))
for case in index['cases']:
    for kind in ('image', 'svg'):
        assert digest(archive/case[kind]) == case[kind+'_sha256'], case['variant']
print(json.dumps(dict(cohorts=summary, archive_pairs=len(index['cases'])), indent=2))
